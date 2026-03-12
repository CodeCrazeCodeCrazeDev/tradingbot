"""
Self-Reflection System

IF I WERE THIS BOT, I WOULD CONSTANTLY ASK MYSELF:
- Why did that trade work/fail?
- What patterns am I missing?
- What am I doing wrong repeatedly?
- What am I doing right that I should do more?
- How can I improve my decision-making process?
- What would a better version of me do differently?

This is my introspection engine - it analyzes my experiences and extracts wisdom.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .experience_memory import (
    ExperienceMemory,
    TradeExperience,
    ExperienceType,
    OutcomeQuality,
    DecisionContext,
)

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights I can discover"""
    PATTERN_DISCOVERED = auto()      # I found a recurring pattern
    MISTAKE_IDENTIFIED = auto()      # I identified a systematic mistake
    SUCCESS_FACTOR = auto()          # I found what makes me successful
    WEAKNESS_FOUND = auto()          # I found a weakness in my approach
    STRENGTH_CONFIRMED = auto()      # I confirmed a strength
    RULE_VIOLATION = auto()          # I violated my own rules
    IMPROVEMENT_OPPORTUNITY = auto() # I found a way to improve
    CORRELATION_FOUND = auto()       # I found a correlation I didn't know about
    BIAS_DETECTED = auto()           # I detected a bias in my decisions


class PatternType(Enum):
    """Types of patterns I can recognize"""
    WINNING_SETUP = auto()           # Conditions that lead to wins
    LOSING_SETUP = auto()            # Conditions that lead to losses
    REGIME_BEHAVIOR = auto()         # How I behave in different regimes
    TIME_PATTERN = auto()            # Time-based patterns
    SEQUENCE_PATTERN = auto()        # Sequence of events pattern
    EMOTIONAL_PATTERN = auto()       # Confidence/fear patterns
    SIZE_PATTERN = auto()            # Position sizing patterns


@dataclass
class ReflectionInsight:
    """An insight discovered through self-reflection"""
    insight_id: str
    insight_type: InsightType
    description: str
    evidence: List[str]  # Experience IDs that support this insight
    confidence: float    # How confident am I in this insight?
    actionable: bool     # Can I act on this insight?
    action_recommendation: str
    impact_estimate: float  # Estimated impact if I act on this
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_id': self.insight_id,
            'insight_type': self.insight_type.name,
            'description': self.description,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'actionable': self.actionable,
            'action_recommendation': self.action_recommendation,
            'impact_estimate': self.impact_estimate,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class PerformancePattern:
    """A pattern in my performance"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    conditions: Dict[str, Any]  # What conditions trigger this pattern
    outcome_distribution: Dict[str, float]  # Distribution of outcomes
    frequency: int  # How often this pattern occurs
    reliability: float  # How reliable is this pattern?
    experience_ids: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type.name,
            'description': self.description,
            'conditions': self.conditions,
            'outcome_distribution': self.outcome_distribution,
            'frequency': self.frequency,
            'reliability': self.reliability,
            'experience_ids': self.experience_ids,
        }


@dataclass
class FailureAnalysis:
    """Deep analysis of a failure"""
    failure_id: str
    experience_id: str
    root_cause: str
    contributing_factors: List[str]
    what_i_should_have_done: str
    lesson_learned: str
    prevention_strategy: str
    severity: float  # How bad was this failure?
    recurrence_risk: float  # Risk of this happening again
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'failure_id': self.failure_id,
            'experience_id': self.experience_id,
            'root_cause': self.root_cause,
            'contributing_factors': self.contributing_factors,
            'what_i_should_have_done': self.what_i_should_have_done,
            'lesson_learned': self.lesson_learned,
            'prevention_strategy': self.prevention_strategy,
            'severity': self.severity,
            'recurrence_risk': self.recurrence_risk,
        }


@dataclass
class SuccessPattern:
    """Analysis of what makes me successful"""
    pattern_id: str
    description: str
    key_factors: List[str]
    optimal_conditions: Dict[str, Any]
    success_rate: float
    average_return: float
    replication_strategy: str
    experience_ids: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'description': self.description,
            'key_factors': self.key_factors,
            'optimal_conditions': self.optimal_conditions,
            'success_rate': self.success_rate,
            'average_return': self.average_return,
            'replication_strategy': self.replication_strategy,
            'experience_ids': self.experience_ids,
        }


class SelfReflector:
    """
    My self-reflection engine.
    
    IF I WERE THIS BOT, I WOULD:
    1. Regularly review my recent experiences
    2. Look for patterns in successes and failures
    3. Identify my biases and blind spots
    4. Question my assumptions
    5. Generate actionable insights
    6. Track whether my insights actually help
    """
    
    def __init__(self, memory: ExperienceMemory, data_dir: str = "self_mastery_data"):
        self.memory = memory
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Store insights
        self.insights: List[ReflectionInsight] = []
        self.patterns: List[PerformancePattern] = []
        self.failure_analyses: List[FailureAnalysis] = []
        self.success_patterns: List[SuccessPattern] = []
        
        # Reflection state
        self.last_reflection_time: Optional[datetime] = None
        self.reflection_count = 0
        
        logger.info("SelfReflector initialized")
    
    def reflect(self, depth: str = "normal") -> List[ReflectionInsight]:
        """
        Perform self-reflection on recent experiences.
        
        depth: "quick" (last hour), "normal" (last day), "deep" (all time)
        """
        logger.info(f"Starting {depth} self-reflection...")
        
        # Get experiences to reflect on
        if depth == "quick":
            experiences = self.memory.recall_recent(hours=1)
        elif depth == "normal":
            experiences = self.memory.recall_recent(hours=24)
        else:  # deep
            experiences = self.memory.recall_recent(hours=24*7, limit=500)
        
        if not experiences:
            logger.info("No experiences to reflect on")
            return []
        
        insights = []
        
        # 1. Analyze failures
        failure_insights = self._analyze_failures(experiences)
        insights.extend(failure_insights)
        
        # 2. Analyze successes
        success_insights = self._analyze_successes(experiences)
        insights.extend(success_insights)
        
        # 3. Find patterns
        pattern_insights = self._find_patterns(experiences)
        insights.extend(pattern_insights)
        
        # 4. Detect biases
        bias_insights = self._detect_biases(experiences)
        insights.extend(bias_insights)
        
        # 5. Check rule compliance
        rule_insights = self._check_rule_compliance(experiences)
        insights.extend(rule_insights)
        
        # 6. Generate improvement opportunities
        improvement_insights = self._generate_improvements(experiences)
        insights.extend(improvement_insights)
        
        # Store insights
        self.insights.extend(insights)
        self.last_reflection_time = datetime.now()
        self.reflection_count += 1
        
        # Save insights to file
        self._save_insights()
        
        logger.info(f"Reflection complete. Generated {len(insights)} insights.")
        
        return insights
    
    def _analyze_failures(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Analyze failures to understand what went wrong"""
        insights = []
        
        # Get experiences with poor outcomes
        failures = [
            exp for exp in experiences
            if exp.outcome and exp.outcome.quality in [OutcomeQuality.POOR, OutcomeQuality.TERRIBLE]
        ]
        
        if not failures:
            return insights
        
        # Group failures by common characteristics
        failure_groups = defaultdict(list)
        
        for failure in failures:
            # Group by regime
            failure_groups[f"regime_{failure.context.regime}"].append(failure)
            # Group by action
            failure_groups[f"action_{failure.action}"].append(failure)
            # Group by confidence level
            conf_bucket = "high" if failure.confidence_at_decision > 0.7 else "medium" if failure.confidence_at_decision > 0.4 else "low"
            failure_groups[f"confidence_{conf_bucket}"].append(failure)
        
        # Analyze each group
        for group_key, group_failures in failure_groups.items():
            if len(group_failures) >= 2:  # Need at least 2 to identify a pattern
                # Create failure analysis
                analysis = self._create_failure_analysis(group_key, group_failures)
                self.failure_analyses.append(analysis)
                
                # Create insight
                insight = ReflectionInsight(
                    insight_id=f"failure_{group_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.MISTAKE_IDENTIFIED,
                    description=f"Repeated failures in {group_key}: {analysis.root_cause}",
                    evidence=[f.experience_id for f in group_failures],
                    confidence=min(0.9, 0.5 + len(group_failures) * 0.1),
                    actionable=True,
                    action_recommendation=analysis.prevention_strategy,
                    impact_estimate=analysis.severity * len(group_failures) * 0.1,
                )
                insights.append(insight)
        
        return insights
    
    def _create_failure_analysis(self, group_key: str, failures: List[TradeExperience]) -> FailureAnalysis:
        """Create detailed failure analysis"""
        # Analyze common factors
        common_factors = []
        
        # Check volatility
        volatilities = [f.context.volatility for f in failures]
        avg_vol = np.mean(volatilities)
        if avg_vol > 0.02:
            common_factors.append("High volatility environment")
        
        # Check drawdown state
        drawdowns = [f.context.drawdown for f in failures]
        avg_dd = np.mean(drawdowns)
        if avg_dd > 0.05:
            common_factors.append("Already in drawdown when trading")
        
        # Check confidence
        confidences = [f.confidence_at_decision for f in failures]
        avg_conf = np.mean(confidences)
        if avg_conf > 0.8:
            common_factors.append("Overconfidence")
        elif avg_conf < 0.4:
            common_factors.append("Low confidence trades")
        
        # Determine root cause
        if "High volatility" in str(common_factors):
            root_cause = "Trading in unsuitable market conditions"
            prevention = "Add volatility filter to avoid trading in high volatility"
        elif "drawdown" in str(common_factors).lower():
            root_cause = "Revenge trading or poor risk management"
            prevention = "Implement cooling-off period after drawdown"
        elif "Overconfidence" in str(common_factors):
            root_cause = "Overconfidence leading to poor risk assessment"
            prevention = "Add confidence calibration and position size limits"
        else:
            root_cause = "Unknown systematic issue"
            prevention = "Gather more data and analyze further"
        
        # Calculate severity
        total_loss = sum(
            f.outcome.pnl for f in failures 
            if f.outcome and f.outcome.pnl < 0
        )
        severity = min(1.0, abs(total_loss) / 10000)  # Normalize
        
        return FailureAnalysis(
            failure_id=f"fa_{group_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            experience_id=failures[0].experience_id,
            root_cause=root_cause,
            contributing_factors=common_factors,
            what_i_should_have_done="Avoided the trade or reduced position size",
            lesson_learned=f"When {', '.join(common_factors)}, be more cautious",
            prevention_strategy=prevention,
            severity=severity,
            recurrence_risk=0.7 if len(failures) > 3 else 0.4,
        )
    
    def _analyze_successes(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Analyze successes to understand what works"""
        insights = []
        
        # Get experiences with good outcomes
        successes = [
            exp for exp in experiences
            if exp.outcome and exp.outcome.quality in [OutcomeQuality.GOOD, OutcomeQuality.EXCELLENT]
        ]
        
        if len(successes) < 3:
            return insights
        
        # Find common success factors
        success_factors = defaultdict(int)
        
        for success in successes:
            # Analyze context
            if success.context.volatility < 0.015:
                success_factors["low_volatility"] += 1
            if success.context.trend in ["up", "down"]:
                success_factors["trending_market"] += 1
            if success.confidence_at_decision > 0.6:
                success_factors["high_confidence"] += 1
            if success.context.drawdown < 0.02:
                success_factors["fresh_capital"] += 1
        
        # Create success patterns for significant factors
        for factor, count in success_factors.items():
            if count >= len(successes) * 0.5:  # Present in 50%+ of successes
                pattern = SuccessPattern(
                    pattern_id=f"sp_{factor}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    description=f"Success associated with {factor}",
                    key_factors=[factor],
                    optimal_conditions={factor: True},
                    success_rate=count / len(successes),
                    average_return=np.mean([s.outcome.pnl_percent for s in successes if s.outcome]),
                    replication_strategy=f"Prioritize trades when {factor} condition is met",
                    experience_ids=[s.experience_id for s in successes],
                )
                self.success_patterns.append(pattern)
                
                insight = ReflectionInsight(
                    insight_id=f"success_{factor}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.SUCCESS_FACTOR,
                    description=f"Success factor identified: {factor}",
                    evidence=[s.experience_id for s in successes],
                    confidence=count / len(successes),
                    actionable=True,
                    action_recommendation=pattern.replication_strategy,
                    impact_estimate=pattern.average_return * pattern.success_rate,
                )
                insights.append(insight)
        
        return insights
    
    def _find_patterns(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Find recurring patterns in experiences"""
        insights = []
        
        if len(experiences) < 10:
            return insights
        
        # Pattern 1: Time-based patterns
        time_performance = defaultdict(list)
        for exp in experiences:
            if exp.outcome:
                hour = exp.context.timestamp.hour
                time_performance[hour].append(exp.outcome.pnl_percent)
        
        # Find best and worst hours
        hour_stats = {
            hour: (np.mean(returns), len(returns))
            for hour, returns in time_performance.items()
            if len(returns) >= 3
        }
        
        if hour_stats:
            best_hour = max(hour_stats.items(), key=lambda x: x[1][0])
            worst_hour = min(hour_stats.items(), key=lambda x: x[1][0])
            
            if best_hour[1][0] > 0.01:  # Significant positive
                insights.append(ReflectionInsight(
                    insight_id=f"time_best_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.PATTERN_DISCOVERED,
                    description=f"Best performance at hour {best_hour[0]} (avg return: {best_hour[1][0]:.2%})",
                    evidence=[],
                    confidence=min(0.9, best_hour[1][1] / 10),
                    actionable=True,
                    action_recommendation=f"Prioritize trading at hour {best_hour[0]}",
                    impact_estimate=best_hour[1][0],
                ))
            
            if worst_hour[1][0] < -0.01:  # Significant negative
                insights.append(ReflectionInsight(
                    insight_id=f"time_worst_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.PATTERN_DISCOVERED,
                    description=f"Worst performance at hour {worst_hour[0]} (avg return: {worst_hour[1][0]:.2%})",
                    evidence=[],
                    confidence=min(0.9, worst_hour[1][1] / 10),
                    actionable=True,
                    action_recommendation=f"Avoid trading at hour {worst_hour[0]}",
                    impact_estimate=abs(worst_hour[1][0]),
                ))
        
        # Pattern 2: Sequence patterns (what happens after wins/losses)
        for i in range(1, len(experiences)):
            prev = experiences[i-1]
            curr = experiences[i]
            
            if prev.outcome and curr.outcome:
                if prev.outcome.quality == OutcomeQuality.TERRIBLE:
                    if curr.outcome.quality in [OutcomeQuality.POOR, OutcomeQuality.TERRIBLE]:
                        # Loss followed by loss - potential tilt
                        insights.append(ReflectionInsight(
                            insight_id=f"tilt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                            insight_type=InsightType.BIAS_DETECTED,
                            description="Possible tilt: losses following losses",
                            evidence=[prev.experience_id, curr.experience_id],
                            confidence=0.6,
                            actionable=True,
                            action_recommendation="Implement mandatory break after significant losses",
                            impact_estimate=0.05,
                        ))
                        break  # Only report once
        
        return insights
    
    def _detect_biases(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Detect cognitive biases in my trading"""
        insights = []
        
        if len(experiences) < 20:
            return insights
        
        # Bias 1: Overtrading
        trades_per_day = defaultdict(int)
        for exp in experiences:
            if exp.experience_type == ExperienceType.TRADE_EXECUTED:
                day = exp.context.timestamp.date()
                trades_per_day[day] += 1
        
        if trades_per_day:
            avg_trades = np.mean(list(trades_per_day.values()))
            if avg_trades > 10:
                insights.append(ReflectionInsight(
                    insight_id=f"bias_overtrade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.BIAS_DETECTED,
                    description=f"Overtrading detected: {avg_trades:.1f} trades/day average",
                    evidence=[],
                    confidence=0.8,
                    actionable=True,
                    action_recommendation="Implement daily trade limits",
                    impact_estimate=0.03,
                ))
        
        # Bias 2: Disposition effect (holding losers, selling winners)
        winners_held = 0
        losers_held = 0
        
        for exp in experiences:
            if exp.outcome:
                if exp.outcome.pnl > 0 and exp.outcome.duration_seconds < 300:
                    winners_held += 1  # Sold winner quickly
                elif exp.outcome.pnl < 0 and exp.outcome.duration_seconds > 3600:
                    losers_held += 1  # Held loser too long
        
        if winners_held > 5 and losers_held > 5:
            if losers_held / (winners_held + 0.1) > 1.5:
                insights.append(ReflectionInsight(
                    insight_id=f"bias_disposition_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.BIAS_DETECTED,
                    description="Disposition effect: holding losers longer than winners",
                    evidence=[],
                    confidence=0.7,
                    actionable=True,
                    action_recommendation="Use time-based stops and let winners run",
                    impact_estimate=0.05,
                ))
        
        # Bias 3: Recency bias
        recent = experiences[:10]
        older = experiences[10:30] if len(experiences) > 30 else []
        
        if recent and older:
            recent_conf = np.mean([e.confidence_at_decision for e in recent])
            older_outcomes = [e.outcome.quality for e in older if e.outcome]
            
            # If recent confidence doesn't match older performance
            older_success_rate = sum(1 for o in older_outcomes if o in [OutcomeQuality.GOOD, OutcomeQuality.EXCELLENT]) / len(older_outcomes) if older_outcomes else 0.5
            
            if abs(recent_conf - older_success_rate) > 0.3:
                insights.append(ReflectionInsight(
                    insight_id=f"bias_recency_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.BIAS_DETECTED,
                    description=f"Recency bias: confidence ({recent_conf:.1%}) doesn't match historical performance ({older_success_rate:.1%})",
                    evidence=[],
                    confidence=0.6,
                    actionable=True,
                    action_recommendation="Calibrate confidence based on longer-term statistics",
                    impact_estimate=0.02,
                ))
        
        return insights
    
    def _check_rule_compliance(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Check if I'm following my own rules"""
        insights = []
        
        # Define rules to check
        rules = [
            ("max_position_size", lambda e: abs(e.context.current_position) <= 1.0, "Position size exceeded limit"),
            ("max_drawdown_trading", lambda e: e.context.drawdown <= 0.1, "Traded while in significant drawdown"),
            ("min_confidence", lambda e: e.confidence_at_decision >= 0.3, "Traded with very low confidence"),
            ("volatility_filter", lambda e: e.context.volatility <= 0.05, "Traded in extreme volatility"),
        ]
        
        for rule_name, rule_check, violation_desc in rules:
            violations = [
                exp for exp in experiences
                if exp.experience_type == ExperienceType.TRADE_EXECUTED and not rule_check(exp)
            ]
            
            if len(violations) >= 3:
                insights.append(ReflectionInsight(
                    insight_id=f"rule_{rule_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    insight_type=InsightType.RULE_VIOLATION,
                    description=f"Rule violation: {violation_desc} ({len(violations)} times)",
                    evidence=[v.experience_id for v in violations],
                    confidence=0.9,
                    actionable=True,
                    action_recommendation=f"Enforce {rule_name} rule more strictly",
                    impact_estimate=0.03 * len(violations),
                ))
        
        return insights
    
    def _generate_improvements(self, experiences: List[TradeExperience]) -> List[ReflectionInsight]:
        """Generate improvement opportunities"""
        insights = []
        
        if len(experiences) < 10:
            return insights
        
        # Calculate overall statistics
        outcomes = [e.outcome for e in experiences if e.outcome]
        if not outcomes:
            return insights
        
        win_rate = sum(1 for o in outcomes if o.quality in [OutcomeQuality.GOOD, OutcomeQuality.EXCELLENT]) / len(outcomes)
        avg_return = np.mean([o.pnl_percent for o in outcomes])
        avg_rr = np.mean([o.risk_reward_ratio for o in outcomes if o.risk_reward_ratio > 0])
        
        # Improvement 1: Win rate
        if win_rate < 0.5:
            insights.append(ReflectionInsight(
                insight_id=f"improve_winrate_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                insight_type=InsightType.IMPROVEMENT_OPPORTUNITY,
                description=f"Win rate is low ({win_rate:.1%}). Need better entry criteria.",
                evidence=[],
                confidence=0.8,
                actionable=True,
                action_recommendation="Tighten entry criteria, require more confirmation signals",
                impact_estimate=(0.5 - win_rate) * 0.5,
            ))
        
        # Improvement 2: Risk/Reward
        if avg_rr < 1.5:
            insights.append(ReflectionInsight(
                insight_id=f"improve_rr_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                insight_type=InsightType.IMPROVEMENT_OPPORTUNITY,
                description=f"Risk/Reward ratio is low ({avg_rr:.2f}). Need better targets.",
                evidence=[],
                confidence=0.7,
                actionable=True,
                action_recommendation="Increase profit targets or tighten stop losses",
                impact_estimate=(1.5 - avg_rr) * 0.1,
            ))
        
        # Improvement 3: Consistency
        returns = [o.pnl_percent for o in outcomes]
        return_std = np.std(returns)
        if return_std > 0.05:
            insights.append(ReflectionInsight(
                insight_id=f"improve_consistency_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                insight_type=InsightType.IMPROVEMENT_OPPORTUNITY,
                description=f"Returns are inconsistent (std: {return_std:.2%}). Need more stable approach.",
                evidence=[],
                confidence=0.6,
                actionable=True,
                action_recommendation="Reduce position sizes, diversify strategies",
                impact_estimate=return_std * 0.5,
            ))
        
        return insights
    
    def get_top_insights(self, n: int = 10) -> List[ReflectionInsight]:
        """Get top N most important insights"""
        sorted_insights = sorted(
            self.insights,
            key=lambda x: x.impact_estimate * x.confidence,
            reverse=True
        )
        return sorted_insights[:n]
    
    def get_actionable_insights(self) -> List[ReflectionInsight]:
        """Get all actionable insights"""
        return [i for i in self.insights if i.actionable]
    
    def _save_insights(self):
        """Save insights to file"""
        insights_file = self.data_dir / "reflection_insights.json"
        with open(insights_file, 'w') as f:
            json.dump([i.to_dict() for i in self.insights[-100:]], f, indent=2)
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Get summary of all reflections"""
        return {
            'total_insights': len(self.insights),
            'insights_by_type': {
                t.name: sum(1 for i in self.insights if i.insight_type == t)
                for t in InsightType
            },
            'total_patterns': len(self.patterns),
            'failure_analyses': len(self.failure_analyses),
            'success_patterns': len(self.success_patterns),
            'last_reflection': self.last_reflection_time.isoformat() if self.last_reflection_time else None,
            'reflection_count': self.reflection_count,
            'top_recommendations': [
                i.action_recommendation for i in self.get_top_insights(5)
            ],
        }
