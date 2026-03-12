"""
Behavioral and Psychological Features for Trading.

This module implements:
- Trader psychology tracking
- Emotional state detection
- Cognitive bias identification
- Behavioral pattern analysis
- Tilt detection
- Discipline scoring
- Mental state optimization
- Performance psychology metrics
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Emotional states affecting trading."""
    CALM = "calm"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    GREEDY = "greedy"
    FRUSTRATED = "frustrated"
    EUPHORIC = "euphoric"
    REVENGE = "revenge"
    FOMO = "fomo"
    PARALYZED = "paralyzed"


class CognitiveBias(Enum):
    """Common cognitive biases in trading."""
    CONFIRMATION = "confirmation"
    RECENCY = "recency"
    ANCHORING = "anchoring"
    LOSS_AVERSION = "loss_aversion"
    OVERCONFIDENCE = "overconfidence"
    HINDSIGHT = "hindsight"
    GAMBLER_FALLACY = "gambler_fallacy"
    SUNK_COST = "sunk_cost"
    DISPOSITION_EFFECT = "disposition_effect"
    HERDING = "herding"


class TiltLevel(Enum):
    """Tilt severity levels."""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class DisciplineArea(Enum):
    """Areas of trading discipline."""
    ENTRY_RULES = "entry_rules"
    EXIT_RULES = "exit_rules"
    POSITION_SIZING = "position_sizing"
    RISK_MANAGEMENT = "risk_management"
    TRADE_MANAGEMENT = "trade_management"
    PATIENCE = "patience"
    CONSISTENCY = "consistency"


@dataclass
class TradeRecord:
    """Record of a trade for psychological analysis."""
    trade_id: str
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    planned_stop: float
    actual_stop: float
    planned_target: float
    actual_target: float
    pnl: float = 0.0
    followed_plan: bool = True
    emotional_state: EmotionalState = EmotionalState.CALM
    notes: str = ""
    
    @property
    def duration(self) -> Optional[timedelta]:
        try:
            if self.exit_time:
                return self.exit_time - self.entry_time
            return None
        except Exception as e:
            logger.error(f"Error in duration: {e}")
            raise
    
    @property
    def r_multiple(self) -> float:
        try:
            if self.planned_stop == self.entry_price:
                return 0.0
            risk = abs(self.entry_price - self.planned_stop)
            return self.pnl / risk if risk > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in r_multiple: {e}")
            raise


@dataclass
class PsychologicalProfile:
    """Trader's psychological profile."""
    emotional_stability: float  # 0-1
    discipline_score: float  # 0-1
    risk_tolerance: float  # 0-1
    patience_score: float  # 0-1
    adaptability: float  # 0-1
    stress_resilience: float  # 0-1
    decision_quality: float  # 0-1
    self_awareness: float  # 0-1
    dominant_biases: List[CognitiveBias] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class TiltAssessment:
    """Assessment of trader tilt."""
    level: TiltLevel
    score: float  # 0-1
    triggers: List[str]
    symptoms: List[str]
    recommended_actions: List[str]
    cool_down_period: int  # minutes
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DisciplineReport:
    """Report on trading discipline."""
    overall_score: float
    area_scores: Dict[DisciplineArea, float]
    violations: List[str]
    improvements: List[str]
    streak_days: int
    best_area: DisciplineArea
    worst_area: DisciplineArea


class EmotionalStateTracker:
    """
    Tracks and analyzes emotional states during trading.
    """
    
    def __init__(self):
        try:
            self.state_history: List[Tuple[datetime, EmotionalState, float]] = []
            self.current_state = EmotionalState.CALM
            self.state_duration: Dict[EmotionalState, float] = {s: 0 for s in EmotionalState}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_state(
        self,
        state: EmotionalState,
        intensity: float = 0.5,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record an emotional state."""
        try:
            ts = timestamp or datetime.now()
            self.state_history.append((ts, state, intensity))
            self.current_state = state
        
            # Update duration tracking
            if len(self.state_history) > 1:
                prev_ts, prev_state, _ = self.state_history[-2]
                duration = (ts - prev_ts).total_seconds() / 60  # minutes
                self.state_duration[prev_state] += duration
        except Exception as e:
            logger.error(f"Error in record_state: {e}")
            raise
    
    def get_dominant_state(self, lookback_minutes: int = 60) -> EmotionalState:
        """Get the dominant emotional state over a period."""
        try:
            cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
            recent = [(ts, state, intensity) for ts, state, intensity in self.state_history 
                      if ts >= cutoff]
        
            if not recent:
                return EmotionalState.CALM
        
            # Weight by intensity and recency
            state_scores: Dict[EmotionalState, float] = {s: 0 for s in EmotionalState}
            now = datetime.now()
        
            for ts, state, intensity in recent:
                recency_weight = 1 - (now - ts).total_seconds() / (lookback_minutes * 60)
                state_scores[state] += intensity * recency_weight
        
            return max(state_scores, key=state_scores.get)
        except Exception as e:
            logger.error(f"Error in get_dominant_state: {e}")
            raise
    
    def detect_emotional_shift(self) -> Optional[Tuple[EmotionalState, EmotionalState]]:
        """Detect significant emotional shifts."""
        try:
            if len(self.state_history) < 2:
                return None
        
            _, prev_state, prev_intensity = self.state_history[-2]
            _, curr_state, curr_intensity = self.state_history[-1]
        
            if prev_state != curr_state:
                return (prev_state, curr_state)
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_emotional_shift: {e}")
            raise
    
    def get_emotional_volatility(self, lookback_minutes: int = 60) -> float:
        """Calculate emotional volatility (frequency of state changes)."""
        try:
            cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
            recent = [entry for entry in self.state_history if entry[0] >= cutoff]
        
            if len(recent) < 2:
                return 0.0
        
            changes = sum(1 for i in range(1, len(recent)) 
                         if recent[i][1] != recent[i-1][1])
        
            return changes / len(recent)
        except Exception as e:
            logger.error(f"Error in get_emotional_volatility: {e}")
            raise


class CognitiveBiasDetector:
    """
    Detects cognitive biases from trading behavior.
    """
    
    def __init__(self):
        try:
            self.trade_history: List[TradeRecord] = []
            self.detected_biases: Dict[CognitiveBias, float] = {b: 0 for b in CognitiveBias}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_trade(self, trade: TradeRecord) -> None:
        """Add a trade for analysis."""
        try:
            self.trade_history.append(trade)
            self._analyze_trade(trade)
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def _analyze_trade(self, trade: TradeRecord) -> None:
        """Analyze a trade for bias indicators."""
        # Disposition effect: holding losers, cutting winners
        try:
            if trade.pnl > 0 and trade.duration and trade.duration < timedelta(hours=1):
                self.detected_biases[CognitiveBias.DISPOSITION_EFFECT] += 0.1
            elif trade.pnl < 0 and trade.duration and trade.duration > timedelta(days=1):
                self.detected_biases[CognitiveBias.DISPOSITION_EFFECT] += 0.2
        
            # Loss aversion: moving stops to avoid losses
            if trade.actual_stop != trade.planned_stop and trade.pnl < 0:
                self.detected_biases[CognitiveBias.LOSS_AVERSION] += 0.2
        except Exception as e:
            logger.error(f"Error in _analyze_trade: {e}")
            raise
        
        # Sunk cost: adding to losing positions
        # Would need position history to detect properly
        
    def detect_confirmation_bias(
        self,
        trade: TradeRecord,
        contrary_signals: int,
        confirming_signals: int
    ) -> float:
        """Detect confirmation bias in trade decision."""
        try:
            if confirming_signals == 0:
                return 0.0
        
            ratio = contrary_signals / confirming_signals
            if ratio > 0.5 and trade.followed_plan:
                # Ignored contrary signals
                return min(1.0, ratio)
        
            return 0.0
        except Exception as e:
            logger.error(f"Error in detect_confirmation_bias: {e}")
            raise
    
    def detect_recency_bias(
        self,
        recent_trades: List[TradeRecord],
        current_decision_matches_recent: bool
    ) -> float:
        """Detect recency bias."""
        try:
            if len(recent_trades) < 3:
                return 0.0
        
            recent_direction = sum(1 for t in recent_trades[-3:] if t.pnl > 0) / 3
        
            if current_decision_matches_recent and recent_direction > 0.7:
                return 0.5
            elif current_decision_matches_recent and recent_direction < 0.3:
                return 0.5
        
            return 0.0
        except Exception as e:
            logger.error(f"Error in detect_recency_bias: {e}")
            raise
    
    def detect_overconfidence(
        self,
        win_rate: float,
        perceived_win_rate: float,
        position_size_trend: List[float]
    ) -> float:
        """Detect overconfidence bias."""
        # Check if perceived win rate is much higher than actual
        try:
            perception_gap = perceived_win_rate - win_rate
        
            # Check if position sizes are increasing after wins
            if len(position_size_trend) >= 3:
                size_increase = (position_size_trend[-1] - position_size_trend[0]) / position_size_trend[0]
            else:
                size_increase = 0
        
            overconfidence = max(0, perception_gap) * 0.5 + max(0, size_increase) * 0.5
            return min(1.0, overconfidence)
        except Exception as e:
            logger.error(f"Error in detect_overconfidence: {e}")
            raise
    
    def get_bias_report(self) -> Dict[str, Any]:
        """Get comprehensive bias report."""
        # Normalize scores
        try:
            max_score = max(self.detected_biases.values()) if self.detected_biases else 1
            normalized = {
                b.value: score / max_score if max_score > 0 else 0
                for b, score in self.detected_biases.items()
            }
        
            # Identify dominant biases
            dominant = [b for b, score in normalized.items() if score > 0.5]
        
            return {
                'bias_scores': normalized,
                'dominant_biases': dominant,
                'total_trades_analyzed': len(self.trade_history),
                'recommendations': self._get_bias_recommendations(dominant)
            }
        except Exception as e:
            logger.error(f"Error in get_bias_report: {e}")
            raise
    
    def _get_bias_recommendations(self, dominant_biases: List[str]) -> List[str]:
        """Get recommendations for addressing biases."""
        try:
            recommendations = []
        
            bias_advice = {
                'disposition_effect': "Use automated exits to avoid holding losers",
                'loss_aversion': "Pre-define stops and don't move them",
                'confirmation': "Actively seek contrary evidence before trading",
                'recency': "Review longer-term statistics, not just recent trades",
                'overconfidence': "Track actual vs perceived performance",
                'anchoring': "Use multiple reference points for analysis",
                'gambler_fallacy': "Each trade is independent - past doesn't predict future",
                'sunk_cost': "Evaluate positions on current merit, not past investment"
            }
        
            for bias in dominant_biases:
                if bias in bias_advice:
                    recommendations.append(bias_advice[bias])
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _get_bias_recommendations: {e}")
            raise


class TiltDetector:
    """
    Detects and manages trader tilt.
    """
    
    def __init__(
        self,
        loss_threshold: int = 3,
        time_window_minutes: int = 60,
        pnl_threshold: float = -0.02
    ):
        try:
            self.loss_threshold = loss_threshold
            self.time_window_minutes = time_window_minutes
            self.pnl_threshold = pnl_threshold
            self.recent_trades: List[TradeRecord] = []
            self.tilt_history: List[TiltAssessment] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_trade(self, trade: TradeRecord) -> None:
        """Add a trade for tilt analysis."""
        try:
            self.recent_trades.append(trade)
        
            # Keep only recent trades
            cutoff = datetime.now() - timedelta(minutes=self.time_window_minutes)
            self.recent_trades = [t for t in self.recent_trades 
                                 if t.entry_time >= cutoff]
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def assess_tilt(
        self,
        current_pnl: float,
        emotional_state: EmotionalState,
        rule_violations: int = 0
    ) -> TiltAssessment:
        """Assess current tilt level."""
        try:
            triggers = []
            symptoms = []
            score = 0.0
        
            # Check consecutive losses
            recent_losses = sum(1 for t in self.recent_trades[-5:] if t.pnl < 0)
            if recent_losses >= self.loss_threshold:
                triggers.append(f"{recent_losses} consecutive losses")
                score += 0.3
        
            # Check P&L drawdown
            if current_pnl < self.pnl_threshold:
                triggers.append(f"P&L down {current_pnl*100:.1f}%")
                score += 0.3
        
            # Check emotional state
            high_risk_states = [
                EmotionalState.REVENGE, EmotionalState.FRUSTRATED,
                EmotionalState.FOMO, EmotionalState.EUPHORIC
            ]
            if emotional_state in high_risk_states:
                triggers.append(f"Emotional state: {emotional_state.value}")
                score += 0.2
        
            # Check rule violations
            if rule_violations > 0:
                triggers.append(f"{rule_violations} rule violations")
                score += 0.1 * rule_violations
        
            # Determine symptoms based on score
            if score > 0.3:
                symptoms.append("Increased trade frequency")
            if score > 0.5:
                symptoms.append("Larger position sizes")
                symptoms.append("Ignoring stop losses")
            if score > 0.7:
                symptoms.append("Revenge trading")
                symptoms.append("Abandoning trading plan")
        
            # Determine level
            if score < 0.2:
                level = TiltLevel.NONE
                cool_down = 0
            elif score < 0.4:
                level = TiltLevel.MILD
                cool_down = 15
            elif score < 0.6:
                level = TiltLevel.MODERATE
                cool_down = 30
            elif score < 0.8:
                level = TiltLevel.SEVERE
                cool_down = 60
            else:
                level = TiltLevel.CRITICAL
                cool_down = 120
        
            # Generate recommendations
            recommendations = self._get_tilt_recommendations(level)
        
            assessment = TiltAssessment(
                level=level,
                score=min(1.0, score),
                triggers=triggers,
                symptoms=symptoms,
                recommended_actions=recommendations,
                cool_down_period=cool_down
            )
        
            self.tilt_history.append(assessment)
            return assessment
        except Exception as e:
            logger.error(f"Error in assess_tilt: {e}")
            raise
    
    def _get_tilt_recommendations(self, level: TiltLevel) -> List[str]:
        """Get recommendations based on tilt level."""
        try:
            recommendations = {
                TiltLevel.NONE: ["Continue trading normally"],
                TiltLevel.MILD: [
                    "Take a 15-minute break",
                    "Review your trading plan",
                    "Reduce position size by 50%"
                ],
                TiltLevel.MODERATE: [
                    "Stop trading for 30 minutes",
                    "Do a breathing exercise",
                    "Review your rules",
                    "Only take A+ setups"
                ],
                TiltLevel.SEVERE: [
                    "Stop trading for at least 1 hour",
                    "Physical exercise recommended",
                    "Journal your thoughts",
                    "Consider stopping for the day"
                ],
                TiltLevel.CRITICAL: [
                    "STOP TRADING IMMEDIATELY",
                    "Close all positions",
                    "Take the rest of the day off",
                    "Review with mentor/coach",
                    "Do not trade tomorrow without review"
                ]
            }
        
            return recommendations.get(level, [])
        except Exception as e:
            logger.error(f"Error in _get_tilt_recommendations: {e}")
            raise
    
    def should_stop_trading(self) -> Tuple[bool, str]:
        """Determine if trader should stop trading."""
        try:
            if not self.tilt_history:
                return False, "No tilt detected"
        
            latest = self.tilt_history[-1]
        
            if latest.level in [TiltLevel.SEVERE, TiltLevel.CRITICAL]:
                return True, f"Tilt level: {latest.level.value}"
        
            return False, f"Tilt level acceptable: {latest.level.value}"
        except Exception as e:
            logger.error(f"Error in should_stop_trading: {e}")
            raise


class DisciplineTracker:
    """
    Tracks trading discipline across multiple areas.
    """
    
    def __init__(self):
        try:
            self.area_scores: Dict[DisciplineArea, List[float]] = {
                area: [] for area in DisciplineArea
            }
            self.violations: List[Tuple[datetime, DisciplineArea, str]] = []
            self.streak_start: Optional[datetime] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_discipline_check(
        self,
        area: DisciplineArea,
        followed: bool,
        violation_description: str = ""
    ) -> None:
        """Record a discipline check."""
        try:
            score = 1.0 if followed else 0.0
            self.area_scores[area].append(score)
        
            if not followed:
                self.violations.append((datetime.now(), area, violation_description))
                self.streak_start = None
            elif self.streak_start is None:
                self.streak_start = datetime.now()
        except Exception as e:
            logger.error(f"Error in record_discipline_check: {e}")
            raise
    
    def get_area_score(self, area: DisciplineArea, lookback: int = 20) -> float:
        """Get discipline score for an area."""
        try:
            scores = self.area_scores[area][-lookback:]
            if not scores:
                return 1.0
            return sum(scores) / len(scores)
        except Exception as e:
            logger.error(f"Error in get_area_score: {e}")
            raise
    
    def get_overall_score(self, lookback: int = 20) -> float:
        """Get overall discipline score."""
        try:
            area_scores = [self.get_area_score(area, lookback) for area in DisciplineArea]
            return sum(area_scores) / len(area_scores)
        except Exception as e:
            logger.error(f"Error in get_overall_score: {e}")
            raise
    
    def get_streak_days(self) -> int:
        """Get current discipline streak in days."""
        try:
            if self.streak_start is None:
                return 0
            return (datetime.now() - self.streak_start).days
        except Exception as e:
            logger.error(f"Error in get_streak_days: {e}")
            raise
    
    def generate_report(self) -> DisciplineReport:
        """Generate discipline report."""
        try:
            area_scores = {area: self.get_area_score(area) for area in DisciplineArea}
        
            best_area = max(area_scores, key=area_scores.get)
            worst_area = min(area_scores, key=area_scores.get)
        
            # Get recent violations
            recent_violations = [
                f"{area.value}: {desc}"
                for ts, area, desc in self.violations[-10:]
            ]
        
            # Generate improvements
            improvements = []
            for area, score in area_scores.items():
                if score < 0.8:
                    improvements.append(f"Improve {area.value} (current: {score:.0%})")
        
            return DisciplineReport(
                overall_score=self.get_overall_score(),
                area_scores=area_scores,
                violations=recent_violations,
                improvements=improvements,
                streak_days=self.get_streak_days(),
                best_area=best_area,
                worst_area=worst_area
            )
        except Exception as e:
            logger.error(f"Error in generate_report: {e}")
            raise


class BehavioralAnalyzer:
    """
    Complete behavioral analysis system.
    """
    
    def __init__(self):
        try:
            self.emotional_tracker = EmotionalStateTracker()
            self.bias_detector = CognitiveBiasDetector()
            self.tilt_detector = TiltDetector()
            self.discipline_tracker = DisciplineTracker()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_trade(self, trade: TradeRecord) -> None:
        """Record a trade for behavioral analysis."""
        try:
            self.bias_detector.add_trade(trade)
            self.tilt_detector.add_trade(trade)
        
            # Record emotional state
            self.emotional_tracker.record_state(trade.emotional_state)
        
            # Check discipline
            self.discipline_tracker.record_discipline_check(
                DisciplineArea.ENTRY_RULES,
                trade.followed_plan,
                "" if trade.followed_plan else "Did not follow entry rules"
            )
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def get_psychological_profile(self) -> PsychologicalProfile:
        """Generate psychological profile."""
        try:
            discipline = self.discipline_tracker.get_overall_score()
            emotional_volatility = self.emotional_tracker.get_emotional_volatility()
        
            bias_report = self.bias_detector.get_bias_report()
            dominant_biases = [CognitiveBias(b) for b in bias_report['dominant_biases']]
        
            # Calculate scores
            emotional_stability = 1 - emotional_volatility
            patience = self.discipline_tracker.get_area_score(DisciplineArea.PATIENCE)
        
            # Identify strengths and weaknesses
            discipline_report = self.discipline_tracker.generate_report()
            strengths = [f"Strong {discipline_report.best_area.value}"]
            weaknesses = [f"Weak {discipline_report.worst_area.value}"]
        
            if dominant_biases:
                weaknesses.extend([f"Prone to {b.value} bias" for b in dominant_biases[:2]])
        
            return PsychologicalProfile(
                emotional_stability=emotional_stability,
                discipline_score=discipline,
                risk_tolerance=0.5,  # Would need more data
                patience_score=patience,
                adaptability=0.5,  # Would need more data
                stress_resilience=emotional_stability * 0.7 + discipline * 0.3,
                decision_quality=discipline * 0.6 + (1 - len(dominant_biases) / 10) * 0.4,
                self_awareness=0.5,  # Would need self-assessment data
                dominant_biases=dominant_biases,
                strengths=strengths,
                weaknesses=weaknesses
            )
        except Exception as e:
            logger.error(f"Error in get_psychological_profile: {e}")
            raise
    
    def should_trade(self) -> Tuple[bool, str, List[str]]:
        """Determine if trader should trade based on psychological state."""
        # Check tilt
        try:
            should_stop, tilt_reason = self.tilt_detector.should_stop_trading()
            if should_stop:
                return False, tilt_reason, ["Take a break", "Review your state"]
        
            # Check emotional state
            dominant_emotion = self.emotional_tracker.get_dominant_state()
            risky_emotions = [
                EmotionalState.REVENGE, EmotionalState.FOMO,
                EmotionalState.EUPHORIC, EmotionalState.FEARFUL
            ]
        
            if dominant_emotion in risky_emotions:
                return False, f"Risky emotional state: {dominant_emotion.value}", [
                    "Wait for emotional state to stabilize",
                    "Practice mindfulness"
                ]
        
            # Check discipline
            discipline = self.discipline_tracker.get_overall_score()
            if discipline < 0.6:
                return False, f"Low discipline score: {discipline:.0%}", [
                    "Review trading rules",
                    "Only take highest conviction trades"
                ]
        
            return True, "Psychological state acceptable", []
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise


# Convenience functions
def assess_trading_readiness(
    recent_pnl: float,
    consecutive_losses: int,
    emotional_state: str = "calm"
) -> Dict[str, Any]:
    """Quick assessment of trading readiness."""
    try:
        analyzer = BehavioralAnalyzer()
    
        # Record emotional state
        state = EmotionalState(emotional_state)
        analyzer.emotional_tracker.record_state(state)
    
        # Assess tilt
        tilt = analyzer.tilt_detector.assess_tilt(
            recent_pnl,
            state,
            rule_violations=0
        )
    
        can_trade, reason, recommendations = analyzer.should_trade()
    
        return {
            'can_trade': can_trade,
            'reason': reason,
            'tilt_level': tilt.level.value,
            'tilt_score': tilt.score,
            'recommendations': recommendations + tilt.recommended_actions,
            'cool_down_minutes': tilt.cool_down_period
        }
    except Exception as e:
        logger.error(f"Error in assess_trading_readiness: {e}")
        raise


def detect_cognitive_biases(trades: List[Dict]) -> Dict[str, float]:
    """Detect cognitive biases from trade history."""
    try:
        detector = CognitiveBiasDetector()
    
        for trade_dict in trades:
            trade = TradeRecord(
                trade_id=trade_dict.get('id', ''),
                symbol=trade_dict.get('symbol', ''),
                direction=trade_dict.get('direction', 'long'),
                entry_time=trade_dict.get('entry_time', datetime.now()),
                exit_time=trade_dict.get('exit_time'),
                entry_price=trade_dict.get('entry_price', 0),
                exit_price=trade_dict.get('exit_price'),
                planned_stop=trade_dict.get('planned_stop', 0),
                actual_stop=trade_dict.get('actual_stop', 0),
                planned_target=trade_dict.get('planned_target', 0),
                actual_target=trade_dict.get('actual_target', 0),
                pnl=trade_dict.get('pnl', 0),
                followed_plan=trade_dict.get('followed_plan', True)
            )
            detector.add_trade(trade)
    
        report = detector.get_bias_report()
        return report['bias_scores']
    except Exception as e:
        logger.error(f"Error in detect_cognitive_biases: {e}")
        raise
