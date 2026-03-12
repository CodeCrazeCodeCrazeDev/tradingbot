"""
Psychological Performance Metrics.

This module implements:
- Trader psychology metrics
- Emotional performance correlation
- Decision quality analysis
- Discipline scoring
- Stress indicators
- Mental performance tracking
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


class MentalState(Enum):
    """Mental states during trading."""
    OPTIMAL = "optimal"
    FOCUSED = "focused"
    DISTRACTED = "distracted"
    STRESSED = "stressed"
    FATIGUED = "fatigued"
    OVERCONFIDENT = "overconfident"
    FEARFUL = "fearful"
    TILTED = "tilted"


class DecisionQuality(Enum):
    """Quality of trading decisions."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    TERRIBLE = "terrible"


class DisciplineLevel(Enum):
    """Discipline levels."""
    EXEMPLARY = "exemplary"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    BROKEN = "broken"


@dataclass
class TradeDecision:
    """Record of a trading decision."""
    trade_id: str
    decision_type: str  # 'entry', 'exit', 'hold', 'skip'
    followed_rules: bool
    emotional_state: MentalState
    confidence_level: float  # 0-1
    time_to_decide: float  # seconds
    was_profitable: Optional[bool] = None
    regret_score: float = 0.0  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PsychologicalMetrics:
    """Comprehensive psychological metrics."""
    mental_state: MentalState
    discipline_score: float  # 0-100
    decision_quality: DecisionQuality
    emotional_stability: float  # 0-1
    focus_score: float  # 0-1
    stress_level: float  # 0-1
    fatigue_level: float  # 0-1
    confidence_calibration: float  # How well confidence matches results
    tilt_probability: float  # 0-1
    optimal_trading_probability: float  # 0-1


@dataclass
class PerformanceCorrelation:
    """Correlation between psychology and performance."""
    mental_state: MentalState
    win_rate: float
    avg_pnl: float
    avg_r_multiple: float
    sample_size: int
    is_significant: bool


@dataclass
class DisciplineReport:
    """Detailed discipline report."""
    overall_score: float
    rule_adherence: float
    position_sizing_discipline: float
    stop_loss_discipline: float
    entry_discipline: float
    exit_discipline: float
    patience_score: float
    violations: List[str]
    improvements: List[str]


class DecisionAnalyzer:
    """
    Analyzes trading decisions for quality.
    """
    
    def __init__(self):
        try:
            self.decisions: List[TradeDecision] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_decision(self, decision: TradeDecision) -> None:
        """Record a trading decision."""
        try:
            self.decisions.append(decision)
        except Exception as e:
            logger.error(f"Error in record_decision: {e}")
            raise
    
    def calculate_decision_quality(
        self,
        followed_rules: bool,
        was_profitable: Optional[bool],
        confidence_level: float,
        time_to_decide: float
    ) -> DecisionQuality:
        """Calculate quality of a decision."""
        try:
            score = 0
        
            # Rule following is most important
            if followed_rules:
                score += 40
        
            # Profitability matters but isn't everything
            if was_profitable is True:
                score += 20
            elif was_profitable is None:
                score += 10  # Neutral
        
            # Confidence calibration
            if was_profitable is not None:
                if (was_profitable and confidence_level > 0.6) or \
                   (not was_profitable and confidence_level < 0.4):
                    score += 20  # Well calibrated
                elif (was_profitable and confidence_level < 0.4) or \
                     (not was_profitable and confidence_level > 0.6):
                    score -= 10  # Poorly calibrated
        
            # Decision time (not too fast, not too slow)
            if 5 < time_to_decide < 60:
                score += 20  # Thoughtful but not overthinking
            elif time_to_decide < 2:
                score -= 10  # Too impulsive
            elif time_to_decide > 300:
                score -= 10  # Analysis paralysis
        
            # Map score to quality
            if score >= 70:
                return DecisionQuality.EXCELLENT
            elif score >= 50:
                return DecisionQuality.GOOD
            elif score >= 30:
                return DecisionQuality.AVERAGE
            elif score >= 10:
                return DecisionQuality.POOR
            else:
                return DecisionQuality.TERRIBLE
        except Exception as e:
            logger.error(f"Error in calculate_decision_quality: {e}")
            raise
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics on decisions."""
        try:
            if not self.decisions:
                return {}
        
            rule_following = sum(1 for d in self.decisions if d.followed_rules) / len(self.decisions)
            avg_confidence = sum(d.confidence_level for d in self.decisions) / len(self.decisions)
            avg_time = sum(d.time_to_decide for d in self.decisions) / len(self.decisions)
        
            profitable = [d for d in self.decisions if d.was_profitable is True]
            unprofitable = [d for d in self.decisions if d.was_profitable is False]
        
            return {
                'total_decisions': len(self.decisions),
                'rule_following_rate': rule_following,
                'avg_confidence': avg_confidence,
                'avg_decision_time': avg_time,
                'profitable_decisions': len(profitable),
                'unprofitable_decisions': len(unprofitable),
                'confidence_when_profitable': sum(d.confidence_level for d in profitable) / len(profitable) if profitable else 0,
                'confidence_when_unprofitable': sum(d.confidence_level for d in unprofitable) / len(unprofitable) if unprofitable else 0
            }
        except Exception as e:
            logger.error(f"Error in get_decision_stats: {e}")
            raise


class EmotionalTracker:
    """
    Tracks emotional states and their impact.
    """
    
    def __init__(self):
        try:
            self.state_history: List[Tuple[datetime, MentalState, float]] = []
            self.performance_by_state: Dict[MentalState, List[float]] = {
                state: [] for state in MentalState
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_state(
        self,
        state: MentalState,
        intensity: float = 0.5,
        pnl: Optional[float] = None
    ) -> None:
        """Record an emotional state."""
        try:
            self.state_history.append((datetime.now(), state, intensity))
        
            if pnl is not None:
                self.performance_by_state[state].append(pnl)
        except Exception as e:
            logger.error(f"Error in record_state: {e}")
            raise
    
    def get_current_state(self) -> MentalState:
        """Get current mental state."""
        try:
            if not self.state_history:
                return MentalState.FOCUSED
        
            return self.state_history[-1][1]
        except Exception as e:
            logger.error(f"Error in get_current_state: {e}")
            raise
    
    def calculate_emotional_stability(self, lookback_hours: int = 4) -> float:
        """Calculate emotional stability score."""
        try:
            cutoff = datetime.now() - timedelta(hours=lookback_hours)
            recent = [s for s in self.state_history if s[0] >= cutoff]
        
            if len(recent) < 2:
                return 1.0
        
            # Count state changes
            changes = sum(1 for i in range(1, len(recent)) if recent[i][1] != recent[i-1][1])
        
            # More changes = less stability
            stability = 1 - (changes / len(recent))
        
            # Penalize negative states
            negative_states = [MentalState.STRESSED, MentalState.TILTED, MentalState.FEARFUL]
            negative_count = sum(1 for s in recent if s[1] in negative_states)
            negative_penalty = negative_count / len(recent) * 0.3
        
            return max(0, stability - negative_penalty)
        except Exception as e:
            logger.error(f"Error in calculate_emotional_stability: {e}")
            raise
    
    def get_performance_correlation(self) -> List[PerformanceCorrelation]:
        """Get correlation between states and performance."""
        try:
            correlations = []
        
            for state, pnls in self.performance_by_state.items():
                if len(pnls) < 5:
                    continue
            
                wins = sum(1 for p in pnls if p > 0)
                win_rate = wins / len(pnls)
                avg_pnl = sum(pnls) / len(pnls)
            
                correlations.append(PerformanceCorrelation(
                    mental_state=state,
                    win_rate=win_rate,
                    avg_pnl=avg_pnl,
                    avg_r_multiple=avg_pnl / 100,  # Simplified
                    sample_size=len(pnls),
                    is_significant=len(pnls) >= 20
                ))
        
            return correlations
        except Exception as e:
            logger.error(f"Error in get_performance_correlation: {e}")
            raise
    
    def detect_tilt(self) -> Tuple[bool, float]:
        """Detect if trader is on tilt."""
        try:
            if len(self.state_history) < 3:
                return False, 0.0
        
            recent = self.state_history[-10:]
        
            # Check for tilt indicators
            tilt_indicators = 0
        
            # Multiple stressed/tilted states
            negative_count = sum(1 for s in recent if s[1] in [MentalState.STRESSED, MentalState.TILTED])
            if negative_count >= 3:
                tilt_indicators += 2
        
            # High intensity negative states
            high_intensity_negative = sum(1 for s in recent if s[1] in [MentalState.STRESSED, MentalState.TILTED] and s[2] > 0.7)
            if high_intensity_negative >= 2:
                tilt_indicators += 2
        
            # Rapid state changes
            changes = sum(1 for i in range(1, len(recent)) if recent[i][1] != recent[i-1][1])
            if changes >= 5:
                tilt_indicators += 1
        
            tilt_probability = min(1.0, tilt_indicators / 5)
            is_tilted = tilt_probability > 0.6
        
            return is_tilted, tilt_probability
        except Exception as e:
            logger.error(f"Error in detect_tilt: {e}")
            raise


class DisciplineTracker:
    """
    Tracks trading discipline.
    """
    
    def __init__(self):
        try:
            self.rule_checks: List[Tuple[str, bool, datetime]] = []
            self.violations: List[Tuple[str, str, datetime]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_rule_check(self, rule: str, followed: bool) -> None:
        """Record a rule check."""
        try:
            self.rule_checks.append((rule, followed, datetime.now()))
        
            if not followed:
                self.violations.append((rule, "Rule not followed", datetime.now()))
        except Exception as e:
            logger.error(f"Error in record_rule_check: {e}")
            raise
    
    def calculate_discipline_score(self, lookback_days: int = 30) -> float:
        """Calculate overall discipline score."""
        try:
            cutoff = datetime.now() - timedelta(days=lookback_days)
            recent = [r for r in self.rule_checks if r[2] >= cutoff]
        
            if not recent:
                return 100.0
        
            followed = sum(1 for r in recent if r[1])
            return (followed / len(recent)) * 100
        except Exception as e:
            logger.error(f"Error in calculate_discipline_score: {e}")
            raise
    
    def get_discipline_by_rule(self) -> Dict[str, float]:
        """Get discipline score by rule type."""
        try:
            rule_stats = {}
        
            for rule, followed, _ in self.rule_checks:
                if rule not in rule_stats:
                    rule_stats[rule] = {'followed': 0, 'total': 0}
                rule_stats[rule]['total'] += 1
                if followed:
                    rule_stats[rule]['followed'] += 1
        
            return {
                rule: stats['followed'] / stats['total'] * 100
                for rule, stats in rule_stats.items()
            }
        except Exception as e:
            logger.error(f"Error in get_discipline_by_rule: {e}")
            raise
    
    def get_discipline_report(self) -> DisciplineReport:
        """Generate comprehensive discipline report."""
        try:
            overall = self.calculate_discipline_score()
            by_rule = self.get_discipline_by_rule()
        
            # Get specific discipline areas
            rule_adherence = by_rule.get('entry_rules', 100) * 0.5 + by_rule.get('exit_rules', 100) * 0.5
            position_sizing = by_rule.get('position_sizing', 100)
            stop_loss = by_rule.get('stop_loss', 100)
            entry = by_rule.get('entry_rules', 100)
            exit_disc = by_rule.get('exit_rules', 100)
            patience = by_rule.get('patience', 100)
        
            # Get recent violations
            recent_violations = [
                f"{v[0]}: {v[1]}"
                for v in self.violations[-10:]
            ]
        
            # Generate improvements
            improvements = []
            if position_sizing < 80:
                improvements.append("Focus on proper position sizing")
            if stop_loss < 80:
                improvements.append("Improve stop loss discipline")
            if patience < 80:
                improvements.append("Work on patience - avoid overtrading")
        
            return DisciplineReport(
                overall_score=overall,
                rule_adherence=rule_adherence,
                position_sizing_discipline=position_sizing,
                stop_loss_discipline=stop_loss,
                entry_discipline=entry,
                exit_discipline=exit_disc,
                patience_score=patience,
                violations=recent_violations,
                improvements=improvements
            )
        except Exception as e:
            logger.error(f"Error in get_discipline_report: {e}")
            raise


class PsychologicalPerformanceSystem:
    """
    Complete psychological performance tracking system.
    """
    
    def __init__(self):
        try:
            self.decision_analyzer = DecisionAnalyzer()
            self.emotional_tracker = EmotionalTracker()
            self.discipline_tracker = DisciplineTracker()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_trade_psychology(
        self,
        trade_id: str,
        decision_type: str,
        followed_rules: bool,
        emotional_state: MentalState,
        confidence: float,
        decision_time: float,
        pnl: Optional[float] = None
    ) -> None:
        """Record psychological data for a trade."""
        try:
            decision = TradeDecision(
                trade_id=trade_id,
                decision_type=decision_type,
                followed_rules=followed_rules,
                emotional_state=emotional_state,
                confidence_level=confidence,
                time_to_decide=decision_time,
                was_profitable=pnl > 0 if pnl is not None else None
            )
        
            self.decision_analyzer.record_decision(decision)
            self.emotional_tracker.record_state(emotional_state, pnl=pnl)
        
            # Record discipline checks
            self.discipline_tracker.record_rule_check('entry_rules', followed_rules)
        except Exception as e:
            logger.error(f"Error in record_trade_psychology: {e}")
            raise
    
    def get_psychological_metrics(self) -> PsychologicalMetrics:
        """Get comprehensive psychological metrics."""
        # Get current state
        try:
            current_state = self.emotional_tracker.get_current_state()
        
            # Calculate scores
            discipline = self.discipline_tracker.calculate_discipline_score()
            stability = self.emotional_tracker.calculate_emotional_stability()
        
            # Decision quality
            decision_stats = self.decision_analyzer.get_decision_stats()
            if decision_stats:
                rule_rate = decision_stats.get('rule_following_rate', 0.5)
                if rule_rate >= 0.9:
                    decision_quality = DecisionQuality.EXCELLENT
                elif rule_rate >= 0.7:
                    decision_quality = DecisionQuality.GOOD
                elif rule_rate >= 0.5:
                    decision_quality = DecisionQuality.AVERAGE
                else:
                    decision_quality = DecisionQuality.POOR
            else:
                decision_quality = DecisionQuality.AVERAGE
        
            # Tilt detection
            is_tilted, tilt_prob = self.emotional_tracker.detect_tilt()
        
            # Calculate other metrics
            focus_score = 1.0 - tilt_prob
            stress_level = tilt_prob
            fatigue_level = 0.3  # Would need more data
        
            # Confidence calibration
            if decision_stats:
                conf_profitable = decision_stats.get('confidence_when_profitable', 0.5)
                conf_unprofitable = decision_stats.get('confidence_when_unprofitable', 0.5)
                calibration = 1 - abs(conf_profitable - conf_unprofitable - 0.2)
            else:
                calibration = 0.5
        
            # Optimal trading probability
            optimal_prob = (
                (discipline / 100) * 0.3 +
                stability * 0.3 +
                (1 - tilt_prob) * 0.2 +
                calibration * 0.2
            )
        
            return PsychologicalMetrics(
                mental_state=current_state,
                discipline_score=discipline,
                decision_quality=decision_quality,
                emotional_stability=stability,
                focus_score=focus_score,
                stress_level=stress_level,
                fatigue_level=fatigue_level,
                confidence_calibration=calibration,
                tilt_probability=tilt_prob,
                optimal_trading_probability=optimal_prob
            )
        except Exception as e:
            logger.error(f"Error in get_psychological_metrics: {e}")
            raise
    
    def should_trade(self) -> Tuple[bool, str, List[str]]:
        """Determine if trader should trade based on psychology."""
        try:
            metrics = self.get_psychological_metrics()
            reasons = []
        
            # Check tilt
            if metrics.tilt_probability > 0.6:
                return False, "High tilt probability", ["Take a break", "Review recent trades"]
        
            # Check discipline
            if metrics.discipline_score < 60:
                return False, "Low discipline score", ["Review trading rules", "Reduce position sizes"]
        
            # Check emotional stability
            if metrics.emotional_stability < 0.4:
                return False, "Emotional instability detected", ["Practice mindfulness", "Wait for calm"]
        
            # Check mental state
            if metrics.mental_state in [MentalState.TILTED, MentalState.STRESSED, MentalState.FATIGUED]:
                return False, f"Suboptimal mental state: {metrics.mental_state.value}", ["Rest", "Reset mentally"]
        
            # All good
            if metrics.optimal_trading_probability > 0.7:
                return True, "Optimal conditions for trading", []
            elif metrics.optimal_trading_probability > 0.5:
                reasons.append("Conditions acceptable but not optimal")
                return True, "Acceptable conditions", reasons
            else:
                return False, "Suboptimal conditions", ["Wait for better mental state"]
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights on psychological performance."""
        try:
            correlations = self.emotional_tracker.get_performance_correlation()
            discipline_report = self.discipline_tracker.get_discipline_report()
            decision_stats = self.decision_analyzer.get_decision_stats()
        
            # Find best and worst states
            if correlations:
                best_state = max(correlations, key=lambda c: c.win_rate)
                worst_state = min(correlations, key=lambda c: c.win_rate)
            else:
                best_state = worst_state = None
        
            return {
                'best_mental_state': best_state.mental_state.value if best_state else None,
                'best_state_win_rate': best_state.win_rate if best_state else None,
                'worst_mental_state': worst_state.mental_state.value if worst_state else None,
                'worst_state_win_rate': worst_state.win_rate if worst_state else None,
                'discipline_score': discipline_report.overall_score,
                'main_violations': discipline_report.violations[:3],
                'improvements_needed': discipline_report.improvements,
                'decision_stats': decision_stats
            }
        except Exception as e:
            logger.error(f"Error in get_performance_insights: {e}")
            raise


# Convenience functions
def assess_trading_readiness() -> Dict[str, Any]:
    """Quick assessment of trading readiness."""
    try:
        system = PsychologicalPerformanceSystem()
    
        can_trade, reason, recommendations = system.should_trade()
        metrics = system.get_psychological_metrics()
    
        return {
            'can_trade': can_trade,
            'reason': reason,
            'recommendations': recommendations,
            'mental_state': metrics.mental_state.value,
            'discipline_score': metrics.discipline_score,
            'tilt_probability': metrics.tilt_probability,
            'optimal_probability': metrics.optimal_trading_probability
        }
    except Exception as e:
        logger.error(f"Error in assess_trading_readiness: {e}")
        raise


def track_trade_psychology(
    trade_id: str,
    emotional_state: str,
    followed_rules: bool,
    confidence: float,
    pnl: Optional[float] = None
) -> Dict[str, Any]:
    """Track psychology for a trade."""
    try:
        system = PsychologicalPerformanceSystem()
    
        state = MentalState(emotional_state)
        system.record_trade_psychology(
            trade_id=trade_id,
            decision_type='trade',
            followed_rules=followed_rules,
            emotional_state=state,
            confidence=confidence,
            decision_time=30,
            pnl=pnl
        )
    
        metrics = system.get_psychological_metrics()
    
        return {
            'recorded': True,
            'current_discipline': metrics.discipline_score,
            'emotional_stability': metrics.emotional_stability,
            'tilt_risk': metrics.tilt_probability
        }
    except Exception as e:
        logger.error(f"Error in track_trade_psychology: {e}")
        raise
