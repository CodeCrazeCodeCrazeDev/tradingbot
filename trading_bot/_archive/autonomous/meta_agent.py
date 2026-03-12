"""
from typing import List, Optional, Tuple
Meta-Agent - Self-Reflective Decision Critique and Improvement

This module implements a meta-agent that critiques the bot's own decisions,
analyzes performance gaps, and generates improvement plans.

Features:
- Decision post-mortems
- Performance gap analysis
- Auto-generated improvement notes
- Cognitive bias detection
- Learning loop integration

Author: Trading Bot Team
Date: 2025-10-23
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
from typing import Tuple

logger = logging.getLogger(__name__)


class DecisionQuality(Enum):
    """Decision quality enum"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class BiasType(Enum):
    """Cognitive bias types"""
    OVERCONFIDENCE = "overconfidence"
    RECENCY = "recency"
    ANCHORING = "anchoring"
    CONFIRMATION = "confirmation"
    SUNK_COST = "sunk_cost"
    AVAILABILITY = "availability"


@dataclass
class Decision:
    """Trading decision data"""
    decision_id: str
    timestamp: datetime
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reasoning: str
    expected_return: float


@dataclass
class DecisionOutcome:
    """Decision outcome data"""
    decision_id: str
    exit_price: float
    actual_return: float
    exit_reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionCritique:
    """Decision critique data"""
    decision_id: str
    quality: DecisionQuality
    score: float  # 0-100
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    detected_biases: List[BiasType] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ImprovementPlan:
    """Auto-generated improvement plan"""
    plan_id: str
    focus_areas: List[str]
    actions: List[str]
    expected_improvement: float  # percentage
    priority: int  # 1-10, higher = more urgent
    created_at: datetime = field(default_factory=datetime.now)
    implemented: bool = False


class MetaAgent:
    """Self-reflective meta-agent for decision critique and improvement"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Decision tracking
        self.decisions: Dict[str, Decision] = {}
        self.outcomes: Dict[str, DecisionOutcome] = {}
        self.critiques: Dict[str, DecisionCritique] = {}
        
        # Improvement tracking
        self.improvement_plans = deque(maxlen=100)
        self.implemented_improvements = []
        
        # Statistics
        self.decision_history = deque(maxlen=1000)
        self.quality_scores = deque(maxlen=1000)
        self.bias_frequency = {}
        
        # Thresholds
        self.poor_decision_threshold = self.config.get('poor_decision_threshold', 0.4)
        self.bias_detection_threshold = self.config.get('bias_detection_threshold', 0.6)
        
        logger.info("Meta-Agent initialized")
    
    async def record_decision(self, decision: Decision) -> str:
        """Record a trading decision"""
        logger.info(f"Recording decision: {decision.decision_id}")
        
        self.decisions[decision.decision_id] = decision
        self.decision_history.append(decision)
        
        return decision.decision_id
    
    async def record_outcome(self, outcome: DecisionOutcome) -> bool:
        """Record decision outcome"""
        if outcome.decision_id not in self.decisions:
            logger.warning(f"Decision not found: {outcome.decision_id}")
            return False
        
        self.outcomes[outcome.decision_id] = outcome
        
        # Automatically critique the decision
        await self.critique_decision(outcome.decision_id)
        
        return True
    
    async def critique_decision(self, decision_id: str) -> Optional[DecisionCritique]:
        """Critique a decision based on outcome"""
        logger.info(f"Critiquing decision: {decision_id}")
        
        if decision_id not in self.decisions or decision_id not in self.outcomes:
            logger.warning(f"Decision or outcome not found: {decision_id}")
            return None
        
        decision = self.decisions[decision_id]
        outcome = self.outcomes[decision_id]
        
        # Calculate decision quality
        quality, score = self._calculate_quality(decision, outcome)
        
        # Detect biases
        biases = await self._detect_biases(decision, outcome)
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(decision, outcome, quality)
        
        # Create critique
        critique = DecisionCritique(
            decision_id=decision_id,
            quality=quality,
            score=score,
            strengths=self._identify_strengths(decision, outcome),
            weaknesses=self._identify_weaknesses(decision, outcome),
            detected_biases=biases,
            improvement_suggestions=suggestions
        )
        
        self.critiques[decision_id] = critique
        self.quality_scores.append(score)
        
        # Track biases
        for bias in biases:
            self.bias_frequency[bias.value] = self.bias_frequency.get(bias.value, 0) + 1
        
        logger.info(f"Critique completed: {decision_id} (quality: {quality.value}, score: {score:.1f})")
        
        return critique
    
    def _calculate_quality(self, decision: Decision, outcome: DecisionOutcome) -> Tuple[DecisionQuality, float]:
        """Calculate decision quality score"""
        # Compare expected vs actual return
        expected = decision.expected_return
        actual = outcome.actual_return
        
        # Accuracy score
        if expected > 0 and actual > 0:
            accuracy = min(1.0, actual / expected)
        elif expected < 0 and actual < 0:
            accuracy = min(1.0, abs(actual) / abs(expected))
        else:
            accuracy = 0.0
        
        # Confidence calibration
        confidence_calibration = 1.0 - abs(decision.confidence - accuracy)
        
        # Overall score
        score = (accuracy * 0.6 + confidence_calibration * 0.4) * 100
        
        # Determine quality level
        if score >= 85:
            quality = DecisionQuality.EXCELLENT
        elif score >= 70:
            quality = DecisionQuality.GOOD
        elif score >= 50:
            quality = DecisionQuality.FAIR
        elif score >= 30:
            quality = DecisionQuality.POOR
        else:
            quality = DecisionQuality.CRITICAL
        
        return quality, score
    
    async def _detect_biases(self, decision: Decision, outcome: DecisionOutcome) -> List[BiasType]:
        """Detect cognitive biases in decision"""
        biases = []
        
        # Overconfidence bias
        if decision.confidence > 0.8 and outcome.actual_return < 0:
            biases.append(BiasType.OVERCONFIDENCE)
        
        # Anchoring bias (entry price too close to stop loss)
        risk = abs(decision.entry_price - decision.stop_loss)
        reward = abs(decision.take_profit - decision.entry_price)
        if risk < reward * 0.2:
            biases.append(BiasType.ANCHORING)
        
        # Recency bias (recent trades influence current decision)
        if len(self.decision_history) > 5:
            recent_decisions = list(self.decision_history)[-5:]
            recent_returns = [
                self.outcomes.get(d.decision_id, DecisionOutcome(d.decision_id, 0, 0, "")).actual_return
                for d in recent_decisions
                if d.decision_id in self.outcomes
            ]
            if recent_returns and sum(recent_returns) > 0 and decision.confidence > 0.8:
                biases.append(BiasType.RECENCY)
        
        # Confirmation bias (reasoning matches expected outcome)
        if "should" in decision.reasoning.lower() and outcome.actual_return > 0:
            biases.append(BiasType.CONFIRMATION)
        
        return biases
    
    def _identify_strengths(self, decision: Decision, outcome: DecisionOutcome) -> List[str]:
        """Identify decision strengths"""
        strengths = []
        
        if outcome.actual_return > 0:
            strengths.append("Profitable trade")
        
        if abs(decision.confidence - (outcome.actual_return / 100)) < 0.2:
            strengths.append("Well-calibrated confidence")
        
        if outcome.actual_return > decision.expected_return:
            strengths.append("Exceeded expectations")
        
        return strengths
    
    def _identify_weaknesses(self, decision: Decision, outcome: DecisionOutcome) -> List[str]:
        """Identify decision weaknesses"""
        weaknesses = []
        
        if outcome.actual_return < 0:
            weaknesses.append("Loss-making trade")
        
        if abs(decision.confidence - (outcome.actual_return / 100)) > 0.3:
            weaknesses.append("Poor confidence calibration")
        
        if outcome.actual_return < decision.expected_return * 0.5:
            weaknesses.append("Significantly underperformed")
        
        return weaknesses
    
    async def _generate_suggestions(self, decision: Decision, outcome: DecisionOutcome, quality: DecisionQuality) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if quality == DecisionQuality.CRITICAL:
            suggestions.append("Review decision-making process")
            suggestions.append("Increase stop loss buffer")
            suggestions.append("Reduce position size")
        
        if quality in [DecisionQuality.POOR, DecisionQuality.CRITICAL]:
            suggestions.append("Improve entry signal validation")
            suggestions.append("Add pre-trade checklist")
            suggestions.append("Increase confidence threshold")
        
        # Risk/reward ratio
        risk = abs(decision.entry_price - decision.stop_loss)
        reward = abs(decision.take_profit - decision.entry_price)
        if reward / risk < 1.5:
            suggestions.append("Improve risk/reward ratio (target 1.5+)")
        
        return suggestions
    
    async def generate_improvement_plan(self) -> Optional[ImprovementPlan]:
        """Generate auto-improvement plan based on critique history"""
        logger.info("Generating improvement plan...")
        
        if not self.critiques:
            logger.warning("No critiques available for improvement plan")
            return None
        
        # Analyze recent critiques
        recent_critiques = list(self.critiques.values())[-20:]
        
        # Calculate average quality
        avg_quality = sum(c.score for c in recent_critiques) / len(recent_critiques)
        
        # Identify focus areas
        focus_areas = []
        
        # Most common biases
        if self.bias_frequency:
            top_biases = sorted(self.bias_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            focus_areas.extend([bias[0] for bias in top_biases])
        
        # Most common weaknesses
        all_weaknesses = []
        for critique in recent_critiques:
            all_weaknesses.extend(critique.weaknesses)
        
        if all_weaknesses:
            from collections import Counter
            weakness_counts = Counter(all_weaknesses)
            focus_areas.extend([w for w, _ in weakness_counts.most_common(3)])
        
        # Generate actions
        actions = []
        for area in focus_areas[:3]:
            if "confidence" in area.lower():
                actions.append("Implement confidence calibration training")
            elif "risk" in area.lower():
                actions.append("Increase minimum risk/reward ratio to 2.0")
            elif "bias" in area.lower():
                actions.append("Add bias detection to pre-trade checks")
            else:
                actions.append(f"Focus on improving: {area}")
        
        # Calculate expected improvement
        expected_improvement = (100 - avg_quality) * 0.3  # 30% of gap
        
        # Create plan
        plan = ImprovementPlan(
            plan_id=f"plan_{datetime.now().timestamp()}",
            focus_areas=focus_areas,
            actions=actions,
            expected_improvement=expected_improvement,
            priority=min(10, max(1, int((100 - avg_quality) / 10)))
        )
        
        self.improvement_plans.append(plan)
        
        logger.info(f"Improvement plan generated: {plan.plan_id}")
        logger.info(f"Expected improvement: {expected_improvement:.1f}%")
        
        return plan
    
    async def get_meta_analysis(self) -> Dict[str, Any]:
        """Get comprehensive meta-analysis"""
        if not self.critiques:
            return {"status": "No data"}
        
        recent_critiques = list(self.critiques.values())[-50:]
        
        avg_score = sum(c.score for c in recent_critiques) / len(recent_critiques)
        
        quality_distribution = {
            "excellent": sum(1 for c in recent_critiques if c.quality == DecisionQuality.EXCELLENT),
            "good": sum(1 for c in recent_critiques if c.quality == DecisionQuality.GOOD),
            "fair": sum(1 for c in recent_critiques if c.quality == DecisionQuality.FAIR),
            "poor": sum(1 for c in recent_critiques if c.quality == DecisionQuality.POOR),
            "critical": sum(1 for c in recent_critiques if c.quality == DecisionQuality.CRITICAL),
        }
        
        return {
            "total_decisions_analyzed": len(self.critiques),
            "average_quality_score": avg_score,
            "quality_distribution": quality_distribution,
            "most_common_biases": sorted(self.bias_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
            "improvement_plans_generated": len(self.improvement_plans),
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_meta_agent = None


def get_meta_agent(config: Optional[Dict] = None) -> MetaAgent:
    """Get or create singleton meta-agent"""
    global _meta_agent
    if _meta_agent is None:
        _meta_agent = MetaAgent(config)
    return _meta_agent
