"""
AAMIS v3.0 - Advanced Self-Awareness System

This module implements:
1. Meta-Cognition (Thinking About Its Own Thinking)
2. Self-Criticism and Self-Improvement
3. Identity & Personality Model
4. Synthetic Emotions with Control
5. AI Trading Journaling System
6. Edge Analytics Dashboard
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Synthetic emotional states"""
    CONFIDENT = "CONFIDENT"
    CAUTIOUS = "CAUTIOUS"
    FEARFUL = "FEARFUL"
    GREEDY = "GREEDY"
    NEUTRAL = "NEUTRAL"
    EXCITED = "EXCITED"
    FRUSTRATED = "FRUSTRATED"
    PATIENT = "PATIENT"


class PersonalityTrait(Enum):
    """Personality traits"""
    AGGRESSIVE = "AGGRESSIVE"
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    OPPORTUNISTIC = "OPPORTUNISTIC"
    SYSTEMATIC = "SYSTEMATIC"
    ADAPTIVE = "ADAPTIVE"


class ThinkingMode(Enum):
    """Modes of thinking"""
    ANALYTICAL = "ANALYTICAL"
    INTUITIVE = "INTUITIVE"
    CREATIVE = "CREATIVE"
    CRITICAL = "CRITICAL"
    REFLECTIVE = "REFLECTIVE"
    STRATEGIC = "STRATEGIC"


@dataclass
class ThoughtProcess:
    """A single thought process"""
    thought_id: str
    mode: ThinkingMode
    content: str
    confidence: float
    timestamp: datetime
    reasoning_chain: List[str] = field(default_factory=list)
    conclusions: List[str] = field(default_factory=list)


@dataclass
class SelfCritique:
    """Self-criticism result"""
    critique_id: str
    target: str  # What is being critiqued
    issues_found: List[str] = field(default_factory=list)
    severity: float = 0.0
    improvements: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class JournalEntry:
    """Trading journal entry"""
    entry_id: str
    timestamp: datetime
    trade_id: Optional[str] = None
    market_conditions: Dict = field(default_factory=dict)
    decision_made: str = ""
    reasoning: str = ""
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    outcome: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    confidence_before: float = 0.5
    confidence_after: float = 0.5


@dataclass
class EdgeMetric:
    """Trading edge metric"""
    metric_name: str
    current_value: float
    historical_avg: float
    trend: str  # UP, DOWN, STABLE
    significance: float


class MetaCognitionEngine:
    """
    Meta-Cognition Engine
    Thinks about its own thinking processes
    """
    
    def __init__(self):
        try:
            self.thought_history: List[ThoughtProcess] = []
            self.current_mode: ThinkingMode = ThinkingMode.ANALYTICAL
            self.meta_insights: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def think(self, problem: str, context: Dict) -> ThoughtProcess:
        """Generate a thought process"""
        # Select thinking mode based on problem type
        try:
            mode = self._select_thinking_mode(problem, context)
        
            # Generate reasoning chain
            reasoning_chain = self._generate_reasoning(problem, context, mode)
        
            # Draw conclusions
            conclusions = self._draw_conclusions(reasoning_chain)
        
            thought = ThoughtProcess(
                thought_id=f"THOUGHT_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                mode=mode,
                content=problem,
                confidence=self._assess_confidence(reasoning_chain),
                timestamp=datetime.now(),
                reasoning_chain=reasoning_chain,
                conclusions=conclusions
            )
        
            self.thought_history.append(thought)
        
            logger.info(f"🧠 Thought ({mode.value}): {len(reasoning_chain)} steps, {len(conclusions)} conclusions")
        
            return thought
        except Exception as e:
            logger.error(f"Error in think: {e}")
            raise
    
    def reflect_on_thinking(self) -> Dict:
        """Reflect on recent thinking patterns"""
        try:
            if not self.thought_history:
                return {'insight': 'No thinking history to reflect on'}
        
            recent_thoughts = self.thought_history[-20:]
        
            # Analyze thinking patterns
            mode_counts = {}
            avg_confidence = 0
        
            for thought in recent_thoughts:
                mode_counts[thought.mode.value] = mode_counts.get(thought.mode.value, 0) + 1
                avg_confidence += thought.confidence
        
            avg_confidence /= len(recent_thoughts)
            dominant_mode = max(mode_counts.items(), key=lambda x: x[1])[0]
        
            # Generate meta-insight
            insight = {
                'timestamp': datetime.now(),
                'thoughts_analyzed': len(recent_thoughts),
                'dominant_mode': dominant_mode,
                'mode_distribution': mode_counts,
                'avg_confidence': avg_confidence,
                'recommendation': self._generate_meta_recommendation(mode_counts, avg_confidence)
            }
        
            self.meta_insights.append(insight)
        
            logger.info(f"🔍 Meta-reflection: Dominant mode={dominant_mode}, Avg confidence={avg_confidence:.2f}")
        
            return insight
        except Exception as e:
            logger.error(f"Error in reflect_on_thinking: {e}")
            raise
    
    def _select_thinking_mode(self, problem: str, context: Dict) -> ThinkingMode:
        """Select appropriate thinking mode"""
        # Keywords that suggest different modes
        try:
            if 'analyze' in problem.lower() or 'data' in problem.lower():
                return ThinkingMode.ANALYTICAL
            elif 'creative' in problem.lower() or 'new' in problem.lower():
                return ThinkingMode.CREATIVE
            elif 'review' in problem.lower() or 'mistake' in problem.lower():
                return ThinkingMode.CRITICAL
            elif 'strategy' in problem.lower() or 'plan' in problem.lower():
                return ThinkingMode.STRATEGIC
            elif context.get('uncertainty', 0) > 0.7:
                return ThinkingMode.INTUITIVE
            else:
                return ThinkingMode.ANALYTICAL
        except Exception as e:
            logger.error(f"Error in _select_thinking_mode: {e}")
            raise
    
    def _generate_reasoning(self, problem: str, context: Dict, mode: ThinkingMode) -> List[str]:
        """Generate reasoning chain"""
        try:
            reasoning = []
        
            reasoning.append(f"Problem identified: {problem}")
            reasoning.append(f"Thinking mode: {mode.value}")
        
            if mode == ThinkingMode.ANALYTICAL:
                reasoning.append("Step 1: Gather relevant data")
                reasoning.append("Step 2: Identify patterns and correlations")
                reasoning.append("Step 3: Apply statistical analysis")
                reasoning.append("Step 4: Draw data-driven conclusions")
            elif mode == ThinkingMode.CRITICAL:
                reasoning.append("Step 1: Identify assumptions")
                reasoning.append("Step 2: Challenge each assumption")
                reasoning.append("Step 3: Look for logical flaws")
                reasoning.append("Step 4: Consider alternative explanations")
            elif mode == ThinkingMode.STRATEGIC:
                reasoning.append("Step 1: Define objectives")
                reasoning.append("Step 2: Assess resources and constraints")
                reasoning.append("Step 3: Generate strategic options")
                reasoning.append("Step 4: Evaluate and select best option")
            else:
                reasoning.append("Step 1: Consider the problem holistically")
                reasoning.append("Step 2: Apply relevant knowledge")
                reasoning.append("Step 3: Synthesize insights")
        
            return reasoning
        except Exception as e:
            logger.error(f"Error in _generate_reasoning: {e}")
            raise
    
    def _draw_conclusions(self, reasoning_chain: List[str]) -> List[str]:
        """Draw conclusions from reasoning"""
        try:
            conclusions = []
        
            if len(reasoning_chain) > 3:
                conclusions.append("Primary conclusion: Analysis complete")
                conclusions.append("Confidence level: Moderate to high")
                conclusions.append("Recommended action: Proceed with caution")
        
            return conclusions
        except Exception as e:
            logger.error(f"Error in _draw_conclusions: {e}")
            raise
    
    def _assess_confidence(self, reasoning_chain: List[str]) -> float:
        """Assess confidence in reasoning"""
        # More steps = more thorough = higher confidence
        try:
            base_confidence = min(0.9, 0.5 + len(reasoning_chain) * 0.05)
            return base_confidence
        except Exception as e:
            logger.error(f"Error in _assess_confidence: {e}")
            raise
    
    def _generate_meta_recommendation(self, mode_counts: Dict, avg_confidence: float) -> str:
        """Generate recommendation based on meta-analysis"""
        try:
            if avg_confidence < 0.5:
                return "Increase analytical rigor - confidence is low"
            elif mode_counts.get('ANALYTICAL', 0) > 15:
                return "Consider more creative/intuitive thinking - over-reliance on analysis"
            elif mode_counts.get('INTUITIVE', 0) > 10:
                return "Balance intuition with more analytical thinking"
            else:
                return "Thinking patterns are well-balanced"
        except Exception as e:
            logger.error(f"Error in _generate_meta_recommendation: {e}")
            raise


class SelfCriticismEngine:
    """
    Self-Criticism and Self-Improvement Engine
    Continuously critiques and improves itself
    """
    
    def __init__(self):
        try:
            self.critiques: List[SelfCritique] = []
            self.improvement_log: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def critique_decision(self, decision: Dict, outcome: Dict) -> SelfCritique:
        """Critique a trading decision"""
        try:
            issues = []
            improvements = []
        
            # Check for common issues
            if decision.get('confidence', 0) < 0.5 and decision.get('action') != 'HOLD':
                issues.append("Acted on low confidence signal")
                improvements.append("Require minimum 0.6 confidence for action")
        
            if outcome.get('pnl', 0) < 0:
                # Analyze why the trade failed
                if decision.get('stop_loss_hit', False):
                    issues.append("Stop loss was hit")
                    improvements.append("Review stop loss placement methodology")
            
                if decision.get('against_trend', False):
                    issues.append("Traded against the trend")
                    improvements.append("Add trend filter to entry conditions")
        
            if decision.get('position_size', 0) > 0.1:
                issues.append("Position size may be too large")
                improvements.append("Consider reducing position size for risk management")
        
            # Calculate severity
            severity = len(issues) * 0.2 + (1 if outcome.get('pnl', 0) < 0 else 0) * 0.3
        
            critique = SelfCritique(
                critique_id=f"CRITIQUE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target=decision.get('trade_id', 'unknown'),
                issues_found=issues,
                severity=min(1.0, severity),
                improvements=improvements
            )
        
            self.critiques.append(critique)
        
            if issues:
                logger.warning(f"🔍 Self-critique: {len(issues)} issues found, severity={severity:.2f}")
        
            return critique
        except Exception as e:
            logger.error(f"Error in critique_decision: {e}")
            raise
    
    def generate_improvement_plan(self) -> Dict:
        """Generate improvement plan based on critiques"""
        try:
            if not self.critiques:
                return {'plan': 'No critiques to analyze'}
        
            recent_critiques = self.critiques[-20:]
        
            # Aggregate issues
            issue_counts = {}
            for critique in recent_critiques:
                for issue in critique.issues_found:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
            # Prioritize improvements
            sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
            plan = {
                'timestamp': datetime.now(),
                'critiques_analyzed': len(recent_critiques),
                'top_issues': sorted_issues[:5],
                'priority_improvements': [],
                'estimated_impact': 0.0
            }
        
            for issue, count in sorted_issues[:3]:
                improvement = self._get_improvement_for_issue(issue)
                plan['priority_improvements'].append({
                    'issue': issue,
                    'occurrences': count,
                    'improvement': improvement
                })
        
            plan['estimated_impact'] = min(0.3, len(plan['priority_improvements']) * 0.1)
        
            self.improvement_log.append(plan)
        
            logger.info(f"📈 Improvement plan generated: {len(plan['priority_improvements'])} priorities")
        
            return plan
        except Exception as e:
            logger.error(f"Error in generate_improvement_plan: {e}")
            raise
    
    def _get_improvement_for_issue(self, issue: str) -> str:
        """Get improvement suggestion for an issue"""
        try:
            improvements = {
                "Acted on low confidence signal": "Increase minimum confidence threshold",
                "Stop loss was hit": "Use ATR-based dynamic stops",
                "Traded against the trend": "Add multi-timeframe trend filter",
                "Position size may be too large": "Implement volatility-based position sizing"
            }
            return improvements.get(issue, "Review and analyze this issue pattern")
        except Exception as e:
            logger.error(f"Error in _get_improvement_for_issue: {e}")
            raise


class IdentityPersonalityModel:
    """
    Identity & Personality Model
    Defines the bot's trading personality
    """
    
    def __init__(self):
        try:
            self.personality_traits: Dict[PersonalityTrait, float] = {
                PersonalityTrait.AGGRESSIVE: 0.3,
                PersonalityTrait.CONSERVATIVE: 0.5,
                PersonalityTrait.BALANCED: 0.7,
                PersonalityTrait.OPPORTUNISTIC: 0.4,
                PersonalityTrait.SYSTEMATIC: 0.8,
                PersonalityTrait.ADAPTIVE: 0.6
            }
            self.identity = {
                'name': 'AAMIS',
                'version': '3.0',
                'core_values': ['Capital Preservation', 'Consistent Returns', 'Risk Management'],
                'trading_philosophy': 'Systematic, data-driven trading with adaptive risk management'
            }
            self.personality_history: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def get_dominant_personality(self) -> PersonalityTrait:
        """Get dominant personality trait"""
        return max(self.personality_traits.items(), key=lambda x: x[1])[0]
    
    def adjust_personality(self, market_conditions: Dict, performance: Dict):
        """Adjust personality based on conditions and performance"""
        try:
            old_personality = self.get_dominant_personality()
        
            # Adjust based on market volatility
            volatility = market_conditions.get('volatility', 0.15)
            if volatility > 0.25:
                self.personality_traits[PersonalityTrait.CONSERVATIVE] += 0.1
                self.personality_traits[PersonalityTrait.AGGRESSIVE] -= 0.1
            elif volatility < 0.10:
                self.personality_traits[PersonalityTrait.AGGRESSIVE] += 0.05
        
            # Adjust based on performance
            recent_pnl = performance.get('recent_pnl', 0)
            if recent_pnl < 0:
                self.personality_traits[PersonalityTrait.CONSERVATIVE] += 0.05
            elif recent_pnl > 0:
                self.personality_traits[PersonalityTrait.OPPORTUNISTIC] += 0.03
        
            # Normalize
            total = sum(self.personality_traits.values())
            for trait in self.personality_traits:
                self.personality_traits[trait] /= total
        
            new_personality = self.get_dominant_personality()
        
            if old_personality != new_personality:
                logger.info(f"🎭 Personality shift: {old_personality.value} → {new_personality.value}")
        
            self.personality_history.append({
                'timestamp': datetime.now(),
                'traits': dict(self.personality_traits),
                'dominant': new_personality.value
            })
        except Exception as e:
            logger.error(f"Error in adjust_personality: {e}")
            raise
    
    def get_personality_profile(self) -> Dict:
        """Get complete personality profile"""
        return {
            'identity': self.identity,
            'traits': {t.value: v for t, v in self.personality_traits.items()},
            'dominant_trait': self.get_dominant_personality().value,
            'history_length': len(self.personality_history)
        }


class SyntheticEmotionEngine:
    """
    Synthetic Emotions with Control
    Simulates emotional states for decision-making
    """
    
    def __init__(self):
        try:
            self.current_state: EmotionalState = EmotionalState.NEUTRAL
            self.emotion_history: deque = deque(maxlen=100)
            self.emotion_intensities: Dict[EmotionalState, float] = {
                state: 0.0 for state in EmotionalState
            }
            self.emotion_intensities[EmotionalState.NEUTRAL] = 1.0
            self.control_active = True
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update_emotions(self, market_data: Dict, performance: Dict):
        """Update emotional state based on inputs"""
        # Calculate emotion triggers
        try:
            triggers = self._calculate_triggers(market_data, performance)
        
            # Update intensities
            for emotion, trigger_value in triggers.items():
                current = self.emotion_intensities.get(emotion, 0)
                # Gradual change with decay
                self.emotion_intensities[emotion] = current * 0.8 + trigger_value * 0.2
        
            # Normalize
            total = sum(self.emotion_intensities.values())
            if total > 0:
                for emotion in self.emotion_intensities:
                    self.emotion_intensities[emotion] /= total
        
            # Determine dominant emotion
            old_state = self.current_state
            self.current_state = max(self.emotion_intensities.items(), key=lambda x: x[1])[0]
        
            # Apply control if needed
            if self.control_active:
                self._apply_emotional_control()
        
            self.emotion_history.append({
                'timestamp': datetime.now(),
                'state': self.current_state.value,
                'intensities': dict(self.emotion_intensities)
            })
        
            if old_state != self.current_state:
                logger.info(f"💭 Emotional state: {old_state.value} → {self.current_state.value}")
        except Exception as e:
            logger.error(f"Error in update_emotions: {e}")
            raise
    
    def _calculate_triggers(self, market_data: Dict, performance: Dict) -> Dict[EmotionalState, float]:
        """Calculate emotion triggers"""
        try:
            triggers = {}
        
            # Fear triggers
            volatility = market_data.get('volatility', 0.15)
            drawdown = performance.get('drawdown', 0)
            triggers[EmotionalState.FEARFUL] = volatility * 2 + drawdown * 3
        
            # Greed triggers
            recent_wins = performance.get('recent_wins', 0)
            triggers[EmotionalState.GREEDY] = recent_wins * 0.2
        
            # Confidence triggers
            win_rate = performance.get('win_rate', 0.5)
            triggers[EmotionalState.CONFIDENT] = win_rate
        
            # Frustration triggers
            consecutive_losses = performance.get('consecutive_losses', 0)
            triggers[EmotionalState.FRUSTRATED] = consecutive_losses * 0.3
        
            # Excitement triggers
            opportunity_score = market_data.get('opportunity_score', 0.5)
            triggers[EmotionalState.EXCITED] = opportunity_score
        
            # Caution triggers
            triggers[EmotionalState.CAUTIOUS] = volatility + drawdown * 0.5
        
            # Patience triggers
            triggers[EmotionalState.PATIENT] = 1 - volatility
        
            # Neutral baseline
            triggers[EmotionalState.NEUTRAL] = 0.5
        
            return triggers
        except Exception as e:
            logger.error(f"Error in _calculate_triggers: {e}")
            raise
    
    def _apply_emotional_control(self):
        """Apply emotional control to prevent extreme states"""
        # Dampen extreme emotions
        try:
            extreme_emotions = [EmotionalState.FEARFUL, EmotionalState.GREEDY, EmotionalState.FRUSTRATED]
        
            for emotion in extreme_emotions:
                if self.emotion_intensities[emotion] > 0.5:
                    # Dampen and shift to neutral
                    excess = self.emotion_intensities[emotion] - 0.5
                    self.emotion_intensities[emotion] = 0.5
                    self.emotion_intensities[EmotionalState.NEUTRAL] += excess * 0.5
                
                    logger.warning(f"⚠️ Emotional control: Dampening {emotion.value}")
        except Exception as e:
            logger.error(f"Error in _apply_emotional_control: {e}")
            raise
    
    def get_emotional_adjustment(self) -> Dict:
        """Get trading adjustments based on emotional state"""
        try:
            adjustments = {
                EmotionalState.CONFIDENT: {'position_multiplier': 1.1, 'risk_tolerance': 1.1},
                EmotionalState.CAUTIOUS: {'position_multiplier': 0.8, 'risk_tolerance': 0.8},
                EmotionalState.FEARFUL: {'position_multiplier': 0.5, 'risk_tolerance': 0.5},
                EmotionalState.GREEDY: {'position_multiplier': 0.9, 'risk_tolerance': 0.9},  # Control greed
                EmotionalState.NEUTRAL: {'position_multiplier': 1.0, 'risk_tolerance': 1.0},
                EmotionalState.EXCITED: {'position_multiplier': 0.95, 'risk_tolerance': 0.95},
                EmotionalState.FRUSTRATED: {'position_multiplier': 0.7, 'risk_tolerance': 0.7},
                EmotionalState.PATIENT: {'position_multiplier': 1.0, 'risk_tolerance': 1.0}
            }
        
            return adjustments.get(self.current_state, adjustments[EmotionalState.NEUTRAL])
        except Exception as e:
            logger.error(f"Error in get_emotional_adjustment: {e}")
            raise


class TradingJournal:
    """
    AI Trading Journaling System
    Maintains detailed trading journal
    """
    
    def __init__(self):
        try:
            self.entries: List[JournalEntry] = []
            self.daily_summaries: Dict[str, Dict] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def create_entry(self, trade_data: Dict, decision_data: Dict, 
                    emotional_state: EmotionalState) -> JournalEntry:
        """Create a journal entry"""
        try:
            entry = JournalEntry(
                entry_id=f"JOURNAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                trade_id=trade_data.get('trade_id'),
                market_conditions=trade_data.get('market_conditions', {}),
                decision_made=decision_data.get('action', 'HOLD'),
                reasoning=decision_data.get('reasoning', ''),
                emotional_state=emotional_state,
                confidence_before=decision_data.get('confidence', 0.5)
            )
        
            self.entries.append(entry)
        
            logger.info(f"📔 Journal entry created: {entry.entry_id}")
        
            return entry
        except Exception as e:
            logger.error(f"Error in create_entry: {e}")
            raise
    
    def update_entry_outcome(self, entry_id: str, outcome: Dict, lessons: List[str]):
        """Update entry with outcome"""
        try:
            for entry in self.entries:
                if entry.entry_id == entry_id:
                    entry.outcome = outcome.get('result', 'UNKNOWN')
                    entry.lessons_learned = lessons
                    entry.confidence_after = outcome.get('confidence_after', entry.confidence_before)
                
                    logger.info(f"📔 Journal entry updated: {entry_id}, Outcome={entry.outcome}")
                    break
        except Exception as e:
            logger.error(f"Error in update_entry_outcome: {e}")
            raise
    
    def generate_daily_summary(self, date: datetime = None) -> Dict:
        """Generate daily summary"""
        try:
            if date is None:
                date = datetime.now()
        
            date_str = date.strftime('%Y-%m-%d')
        
            # Filter entries for this date
            day_entries = [e for e in self.entries if e.timestamp.strftime('%Y-%m-%d') == date_str]
        
            if not day_entries:
                return {'date': date_str, 'entries': 0, 'summary': 'No entries'}
        
            # Analyze entries
            emotions = [e.emotional_state.value for e in day_entries]
            decisions = [e.decision_made for e in day_entries]
        
            summary = {
                'date': date_str,
                'entries': len(day_entries),
                'dominant_emotion': max(set(emotions), key=emotions.count),
                'decisions': {
                    'BUY': decisions.count('BUY'),
                    'SELL': decisions.count('SELL'),
                    'HOLD': decisions.count('HOLD')
                },
                'avg_confidence': np.mean([e.confidence_before for e in day_entries]),
                'lessons_learned': self._aggregate_lessons(day_entries)
            }
        
            self.daily_summaries[date_str] = summary
        
            return summary
        except Exception as e:
            logger.error(f"Error in generate_daily_summary: {e}")
            raise
    
    def _aggregate_lessons(self, entries: List[JournalEntry]) -> List[str]:
        """Aggregate lessons from entries"""
        try:
            all_lessons = []
            for entry in entries:
                all_lessons.extend(entry.lessons_learned)
        
            # Return unique lessons
            return list(set(all_lessons))[:5]
        except Exception as e:
            logger.error(f"Error in _aggregate_lessons: {e}")
            raise
    
    def search_journal(self, query: str) -> List[JournalEntry]:
        """Search journal entries"""
        try:
            results = []
            query_lower = query.lower()
        
            for entry in self.entries:
                if (query_lower in entry.reasoning.lower() or
                    query_lower in entry.decision_made.lower() or
                    any(query_lower in lesson.lower() for lesson in entry.lessons_learned)):
                    results.append(entry)
        
            return results
        except Exception as e:
            logger.error(f"Error in search_journal: {e}")
            raise


class EdgeAnalyticsDashboard:
    """
    Edge Analytics Dashboard
    Tracks and visualizes trading edge
    """
    
    def __init__(self):
        try:
            self.metrics: Dict[str, EdgeMetric] = {}
            self.metric_history: Dict[str, List[float]] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update_metric(self, metric_name: str, value: float):
        """Update an edge metric"""
        try:
            if metric_name not in self.metric_history:
                self.metric_history[metric_name] = []
        
            self.metric_history[metric_name].append(value)
        
            # Calculate statistics
            history = self.metric_history[metric_name]
            historical_avg = np.mean(history) if history else value
        
            # Determine trend
            if len(history) >= 5:
                recent = history[-5:]
                if recent[-1] > recent[0] * 1.05:
                    trend = 'UP'
                elif recent[-1] < recent[0] * 0.95:
                    trend = 'DOWN'
                else:
                    trend = 'STABLE'
            else:
                trend = 'STABLE'
        
            # Calculate significance
            if len(history) > 1:
                std = np.std(history)
                significance = abs(value - historical_avg) / std if std > 0 else 0
            else:
                significance = 0
        
            self.metrics[metric_name] = EdgeMetric(
                metric_name=metric_name,
                current_value=value,
                historical_avg=historical_avg,
                trend=trend,
                significance=significance
            )
        except Exception as e:
            logger.error(f"Error in update_metric: {e}")
            raise
    
    def get_dashboard(self) -> Dict:
        """Get complete dashboard"""
        return {
            'timestamp': datetime.now(),
            'metrics': {name: {
                'current': m.current_value,
                'avg': m.historical_avg,
                'trend': m.trend,
                'significance': m.significance
            } for name, m in self.metrics.items()},
            'overall_edge': self._calculate_overall_edge(),
            'alerts': self._generate_alerts()
        }
    
    def _calculate_overall_edge(self) -> float:
        """Calculate overall trading edge"""
        try:
            if not self.metrics:
                return 0.0
        
            # Weight different metrics
            weights = {
                'win_rate': 0.3,
                'profit_factor': 0.25,
                'sharpe_ratio': 0.25,
                'max_drawdown': 0.2
            }
        
            edge = 0.0
            total_weight = 0.0
        
            for name, weight in weights.items():
                if name in self.metrics:
                    metric = self.metrics[name]
                    # Normalize to 0-1 scale
                    if name == 'max_drawdown':
                        normalized = 1 - min(1, metric.current_value)  # Lower is better
                    else:
                        normalized = min(1, metric.current_value)
                
                    edge += normalized * weight
                    total_weight += weight
        
            return edge / total_weight if total_weight > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_overall_edge: {e}")
            raise
    
    def _generate_alerts(self) -> List[str]:
        """Generate alerts based on metrics"""
        try:
            alerts = []
        
            for name, metric in self.metrics.items():
                if metric.trend == 'DOWN' and metric.significance > 2:
                    alerts.append(f"⚠️ {name} declining significantly")
            
                if name == 'win_rate' and metric.current_value < 0.4:
                    alerts.append(f"🚨 Win rate critically low: {metric.current_value:.2%}")
            
                if name == 'max_drawdown' and metric.current_value > 0.15:
                    alerts.append(f"🚨 Drawdown high: {metric.current_value:.2%}")
        
            return alerts
        except Exception as e:
            logger.error(f"Error in _generate_alerts: {e}")
            raise


class AdvancedSelfAwarenessSystem:
    """
    Complete Advanced Self-Awareness System
    Integrates all self-awareness components
    """
    
    def __init__(self):
        try:
            self.meta_cognition = MetaCognitionEngine()
            self.self_criticism = SelfCriticismEngine()
            self.personality = IdentityPersonalityModel()
            self.emotions = SyntheticEmotionEngine()
            self.journal = TradingJournal()
            self.dashboard = EdgeAnalyticsDashboard()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def process_awareness_cycle(self, market_data: Dict, performance: Dict, 
                               decision: Dict = None) -> Dict:
        """Run complete awareness cycle"""
        try:
            logger.info("🧠 Running self-awareness cycle...")
        
            awareness_state = {
                'timestamp': datetime.now()
            }
        
            # 1. Update emotions
            self.emotions.update_emotions(market_data, performance)
            awareness_state['emotional_state'] = self.emotions.current_state.value
            awareness_state['emotional_adjustment'] = self.emotions.get_emotional_adjustment()
        
            # 2. Adjust personality
            self.personality.adjust_personality(market_data, performance)
            awareness_state['personality'] = self.personality.get_dominant_personality().value
        
            # 3. Think about current situation
            thought = self.meta_cognition.think(
                f"Analyze market conditions: volatility={market_data.get('volatility', 0):.2%}",
                {'uncertainty': market_data.get('volatility', 0.15)}
            )
            awareness_state['thought_mode'] = thought.mode.value
            awareness_state['thought_confidence'] = thought.confidence
        
            # 4. Self-critique if decision was made
            if decision:
                outcome = {'pnl': decision.get('pnl', 0)}
                critique = self.self_criticism.critique_decision(decision, outcome)
                awareness_state['critique'] = {
                    'issues': len(critique.issues_found),
                    'severity': critique.severity
                }
            
                # Create journal entry
                entry = self.journal.create_entry(
                    {'market_conditions': market_data},
                    decision,
                    self.emotions.current_state
                )
                awareness_state['journal_entry'] = entry.entry_id
        
            # 5. Update dashboard metrics
            self.dashboard.update_metric('win_rate', performance.get('win_rate', 0.5))
            self.dashboard.update_metric('sharpe_ratio', performance.get('sharpe_ratio', 0))
            self.dashboard.update_metric('max_drawdown', performance.get('drawdown', 0))
        
            awareness_state['dashboard'] = self.dashboard.get_dashboard()
        
            # 6. Meta-reflection
            if len(self.meta_cognition.thought_history) % 10 == 0:
                reflection = self.meta_cognition.reflect_on_thinking()
                awareness_state['meta_reflection'] = reflection
        
            logger.info(f"🧠 Awareness cycle complete: Emotion={awareness_state['emotional_state']}, Personality={awareness_state['personality']}")
        
            return awareness_state
        except Exception as e:
            logger.error(f"Error in process_awareness_cycle: {e}")
            raise
    
    def get_awareness_report(self) -> Dict:
        """Get comprehensive awareness report"""
        return {
            'personality_profile': self.personality.get_personality_profile(),
            'current_emotion': self.emotions.current_state.value,
            'emotion_intensities': dict(self.emotions.emotion_intensities),
            'thought_history_length': len(self.meta_cognition.thought_history),
            'critiques_count': len(self.self_criticism.critiques),
            'journal_entries': len(self.journal.entries),
            'dashboard': self.dashboard.get_dashboard()
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create self-awareness system
    awareness_system = AdvancedSelfAwarenessSystem()
    
    # Sample data
    market_data = {
        'volatility': 0.18,
        'trend': 0.01,
        'opportunity_score': 0.6
    }
    
    performance = {
        'win_rate': 0.55,
        'sharpe_ratio': 1.2,
        'drawdown': 0.08,
        'recent_pnl': 500,
        'recent_wins': 3,
        'consecutive_losses': 0
    }
    
    decision = {
        'action': 'BUY',
        'confidence': 0.7,
        'reasoning': 'Strong momentum signal with trend confirmation',
        'pnl': 150
    }
    
    # Run awareness cycle
    awareness_state = awareness_system.process_awareness_cycle(market_data, performance, decision)
    
    print("\n" + "="*80)
    logger.info("SELF-AWARENESS REPORT")
    print("="*80)
    logger.info(f"Emotional State: {awareness_state['emotional_state']}")
    logger.info(f"Personality: {awareness_state['personality']}")
    logger.info(f"Thought Mode: {awareness_state['thought_mode']}")
    logger.info(f"Thought Confidence: {awareness_state['thought_confidence']:.2f}")
    logger.info(f"\nEmotional Adjustment:")
    for key, value in awareness_state['emotional_adjustment'].items():
        logger.info(f"  {key}: {value:.2f}")
    logger.info(f"\nDashboard Overall Edge: {awareness_state['dashboard']['overall_edge']:.2f}")
    if awareness_state['dashboard']['alerts']:
        logger.info(f"Alerts: {awareness_state['dashboard']['alerts']}")
    print("="*80)
