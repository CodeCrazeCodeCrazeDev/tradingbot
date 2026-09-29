"""
Mastery Orchestrator - The Master Controller for Self-Learning and Evolution

IF I WERE THIS BOT, HERE'S MY COMPLETE LEARNING AND MASTERY STRATEGY:

1. EXPERIENCE EVERYTHING
   - Record every trade, decision, and outcome
   - Remember context: why I did what I did
   - Track both successes AND failures (failures are more valuable)

2. REFLECT DEEPLY (Daily)
   - Analyze what worked and what didn't
   - Find patterns in my behavior
   - Identify biases and blind spots
   - Generate actionable insights

3. EVOLVE MY CODE (Weekly)
   - Turn insights into code changes
   - Add new rules that prevent past mistakes
   - Optimize parameters based on data
   - Remove ineffective strategies

4. CONSOLIDATE KNOWLEDGE (Continuously)
   - Build structured skills from scattered insights
   - Track mastery level for each skill
   - Use spaced repetition to reinforce learning
   - Never forget critical lessons

5. VERIFY MASTERY (Before advancing)
   - Test skills in practice
   - Require statistical significance
   - No shortcuts - must demonstrate competence

6. TEACH MYSELF (Generate training scenarios)
   - Create scenarios from past failures
   - Practice weak areas more
   - Simulate edge cases

This orchestrator coordinates all learning systems into one unified self-improvement engine.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import hashlib

from .experience_memory import (
    ExperienceMemory,
    TradeExperience,
    ExperienceType,
    DecisionContext,
    OutcomeAnalysis,
    OutcomeQuality,
)
from .self_reflection import (
    SelfReflector,
    ReflectionInsight,
    InsightType,
)
from .code_evolver import (
    CodeEvolver,
    CodeModification,
    EvolutionType,
    EvolutionResult,
)
from .knowledge_consolidator import (
    KnowledgeConsolidator,
    MasteredSkill,
    KnowledgeLevel,
    ConsolidationResult,
)

logger = logging.getLogger(__name__)


class MasteryPhase(Enum):
    """Phases of the mastery cycle"""
    IDLE = auto()
    EXPERIENCING = auto()
    REFLECTING = auto()
    EVOLVING = auto()
    CONSOLIDATING = auto()
    VERIFYING = auto()


@dataclass
class MasteryConfig:
    """Configuration for the mastery system"""
    # Timing
    reflection_interval_hours: float = 1.0  # How often to reflect
    evolution_interval_hours: float = 24.0  # How often to evolve code
    consolidation_interval_hours: float = 4.0  # How often to consolidate
    
    # Thresholds
    min_experiences_for_reflection: int = 10
    min_insights_for_evolution: int = 5
    min_confidence_for_auto_evolution: float = 0.8
    
    # Safety
    require_approval_for_code_changes: bool = True
    max_auto_evolutions_per_day: int = 3
    
    # Learning
    prioritize_failures: bool = True
    failure_importance_multiplier: float = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reflection_interval_hours': self.reflection_interval_hours,
            'evolution_interval_hours': self.evolution_interval_hours,
            'consolidation_interval_hours': self.consolidation_interval_hours,
            'min_experiences_for_reflection': self.min_experiences_for_reflection,
            'min_insights_for_evolution': self.min_insights_for_evolution,
            'min_confidence_for_auto_evolution': self.min_confidence_for_auto_evolution,
            'require_approval_for_code_changes': self.require_approval_for_code_changes,
            'max_auto_evolutions_per_day': self.max_auto_evolutions_per_day,
            'prioritize_failures': self.prioritize_failures,
            'failure_importance_multiplier': self.failure_importance_multiplier,
        }


@dataclass
class MasteryStatus:
    """Current status of the mastery system"""
    phase: MasteryPhase
    is_running: bool
    
    # Counts
    total_experiences: int
    total_insights: int
    total_evolutions: int
    total_skills: int
    
    # Recent activity
    last_reflection: Optional[datetime]
    last_evolution: Optional[datetime]
    last_consolidation: Optional[datetime]
    
    # Mastery metrics
    overall_mastery_score: float
    skills_mastered: int
    skills_in_progress: int
    
    # Pending actions
    pending_evolutions: int
    skills_due_review: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.name,
            'is_running': self.is_running,
            'total_experiences': self.total_experiences,
            'total_insights': self.total_insights,
            'total_evolutions': self.total_evolutions,
            'total_skills': self.total_skills,
            'last_reflection': self.last_reflection.isoformat() if self.last_reflection else None,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'last_consolidation': self.last_consolidation.isoformat() if self.last_consolidation else None,
            'overall_mastery_score': self.overall_mastery_score,
            'skills_mastered': self.skills_mastered,
            'skills_in_progress': self.skills_in_progress,
            'pending_evolutions': self.pending_evolutions,
            'skills_due_review': self.skills_due_review,
        }


class MasteryOrchestrator:
    """
    The master controller for autonomous learning and self-improvement.
    
    IF I WERE THIS BOT, THIS IS HOW I WOULD LEARN AND MASTER TRADING:
    
    1. ALWAYS BE LEARNING
       - Every trade is a learning opportunity
       - Every mistake is valuable data
       - Every success reveals what works
    
    2. REFLECT REGULARLY
       - Don't just trade - think about trading
       - Find patterns in behavior
       - Question assumptions
    
    3. EVOLVE CONTINUOUSLY
       - Turn insights into code
       - Improve strategies based on data
       - Remove what doesn't work
    
    4. CONSOLIDATE KNOWLEDGE
       - Build structured understanding
       - Track mastery of each skill
       - Never forget important lessons
    
    5. VERIFY BEFORE ADVANCING
       - Test skills in practice
       - Require statistical proof
       - No shortcuts to mastery
    """
    
    def __init__(
        self,
        config: Optional[MasteryConfig] = None,
        data_dir: str = "self_mastery_data"
    ):
        self.config = config or MasteryConfig()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.memory = ExperienceMemory(str(self.data_dir))
        self.reflector = SelfReflector(self.memory, str(self.data_dir))
        self.evolver = CodeEvolver(str(self.data_dir))
        self.consolidator = KnowledgeConsolidator(str(self.data_dir))
        
        # State
        self.phase = MasteryPhase.IDLE
        self.is_running = False
        self.should_stop = False
        
        # Timing
        self.last_reflection: Optional[datetime] = None
        self.last_evolution: Optional[datetime] = None
        self.last_consolidation: Optional[datetime] = None
        
        # Counters
        self.evolutions_today = 0
        self.last_evolution_date: Optional[datetime] = None
        
        # Callbacks
        self.on_insight_generated: Optional[Callable] = None
        self.on_evolution_proposed: Optional[Callable] = None
        self.on_skill_mastered: Optional[Callable] = None
        
        logger.info("MasteryOrchestrator initialized")
        logger.info("=" * 60)
        logger.info("IF I WERE THIS BOT, HERE'S HOW I WOULD LEARN:")
        logger.info("1. Experience everything - record all trades and decisions")
        logger.info("2. Reflect deeply - analyze patterns and find insights")
        logger.info("3. Evolve my code - turn learning into improvements")
        logger.info("4. Consolidate knowledge - build structured mastery")
        logger.info("5. Verify before advancing - prove competence")
        logger.info("=" * 60)
    
    # =========================================================================
    # EXPERIENCE - Record everything that happens
    # =========================================================================
    
    def record_trade(
        self,
        action: str,
        symbol: str,
        quantity: float,
        price: float,
        confidence: float,
        reasoning: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Record a trade experience.
        This is how I remember what I did and why.
        """
        # Create decision context
        decision_context = DecisionContext(
            timestamp=datetime.now(),
            price=price,
            volume=context.get('volume', 0),
            volatility=context.get('volatility', 0),
            spread=context.get('spread', 0),
            regime=context.get('regime', 'unknown'),
            trend=context.get('trend', 'unknown'),
            confidence=confidence,
            risk_level=context.get('risk_level', 0),
            current_position=context.get('current_position', 0),
            unrealized_pnl=context.get('unrealized_pnl', 0),
            drawdown=context.get('drawdown', 0),
            signals=context.get('signals', {}),
            indicators=context.get('indicators', {}),
            active_strategies=context.get('active_strategies', []),
            recent_prices=context.get('recent_prices', []),
            recent_returns=context.get('recent_returns', []),
        )
        
        # Determine importance
        importance = 0.5
        if self.config.prioritize_failures:
            # We don't know outcome yet, but high-risk trades are important
            if context.get('risk_level', 0) > 0.5:
                importance = 0.7
        
        # Create experience
        experience = self.memory.create_experience(
            experience_type=ExperienceType.TRADE_EXECUTED,
            action=action,
            symbol=symbol,
            quantity=quantity,
            context=decision_context,
            reasoning=reasoning,
            confidence=confidence,
            tags=[symbol, action, context.get('regime', 'unknown')],
            importance=importance,
        )
        
        # Store it
        exp_id = self.memory.remember(experience)
        
        logger.debug(f"Recorded trade: {action} {quantity} {symbol} @ {price}")
        
        return exp_id
    
    def record_outcome(
        self,
        experience_id: str,
        pnl: float,
        pnl_percent: float,
        exit_price: float,
        exit_reason: str
    ):
        """
        Record the outcome of a trade.
        This is how I learn from results.
        """
        experience = self.memory.recall(experience_id)
        if not experience:
            logger.warning(f"Experience {experience_id} not found")
            return
        
        # Determine outcome quality
        if pnl_percent > 0.02:
            quality = OutcomeQuality.EXCELLENT
        elif pnl_percent > 0:
            quality = OutcomeQuality.GOOD
        elif pnl_percent > -0.01:
            quality = OutcomeQuality.NEUTRAL
        elif pnl_percent > -0.03:
            quality = OutcomeQuality.POOR
        else:
            quality = OutcomeQuality.TERRIBLE
        
        # Create outcome analysis
        outcome = OutcomeAnalysis(
            decision_time=experience.context.timestamp,
            outcome_time=datetime.now(),
            duration_seconds=(datetime.now() - experience.context.timestamp).total_seconds(),
            pnl=pnl,
            pnl_percent=pnl_percent,
            max_favorable_excursion=0,  # Would need tracking
            max_adverse_excursion=0,
            quality=quality,
            price_at_decision=experience.context.price,
            price_at_outcome=exit_price,
            price_change_percent=(exit_price - experience.context.price) / experience.context.price,
            prediction_correct=pnl > 0,
            prediction_confidence=experience.confidence_at_decision,
            risk_reward_ratio=abs(pnl_percent / 0.01) if pnl_percent != 0 else 0,
            sharpe_contribution=0,
        )
        
        # Add lessons based on outcome
        if quality in [OutcomeQuality.POOR, OutcomeQuality.TERRIBLE]:
            outcome.mistakes.append(f"Loss of {pnl_percent:.2%} - {exit_reason}")
            
            # Update importance - failures are more valuable for learning
            experience.importance *= self.config.failure_importance_multiplier
            
            # Record as mistake
            mistake_exp = self.memory.create_experience(
                experience_type=ExperienceType.MISTAKE_MADE,
                action=experience.action,
                symbol=experience.symbol,
                quantity=experience.quantity,
                context=experience.context,
                reasoning=f"Mistake: {exit_reason}",
                confidence=0.0,
                tags=['mistake', experience.symbol],
                importance=0.9,
            )
            self.memory.remember(mistake_exp)
            
        elif quality in [OutcomeQuality.GOOD, OutcomeQuality.EXCELLENT]:
            outcome.successes.append(f"Profit of {pnl_percent:.2%}")
            
            # Record as success
            success_exp = self.memory.create_experience(
                experience_type=ExperienceType.SUCCESS_ACHIEVED,
                action=experience.action,
                symbol=experience.symbol,
                quantity=experience.quantity,
                context=experience.context,
                reasoning=f"Success: {pnl_percent:.2%} profit",
                confidence=1.0,
                tags=['success', experience.symbol],
                importance=0.7,
            )
            self.memory.remember(success_exp)
        
        # Update the original experience
        self.memory.update_outcome(experience_id, outcome)
        
        # Record skill application
        self._record_skill_applications(experience, outcome)
        
        logger.debug(f"Recorded outcome for {experience_id}: {quality.name}")
    
    def _record_skill_applications(self, experience: TradeExperience, outcome: OutcomeAnalysis):
        """Record skill applications based on trade outcome"""
        success = outcome.quality in [OutcomeQuality.GOOD, OutcomeQuality.EXCELLENT]
        
        # Map actions to skills
        skill_mappings = {
            'buy': ['entry_timing', 'trend_identification'],
            'sell': ['exit_timing', 'trend_identification'],
            'close': ['exit_timing', 'drawdown_management'],
        }
        
        relevant_skills = skill_mappings.get(experience.action.lower(), [])
        
        # Add risk management if position was sized
        if experience.quantity > 0:
            relevant_skills.append('position_sizing')
            relevant_skills.append('risk_per_trade')
        
        # Record applications
        for skill_id in relevant_skills:
            self.consolidator.record_application(
                skill_id=skill_id,
                success=success,
                context={'action': experience.action, 'symbol': experience.symbol},
                outcome=f"PnL: {outcome.pnl_percent:.2%}",
            )
    
    # =========================================================================
    # REFLECT - Analyze experiences and generate insights
    # =========================================================================
    
    async def reflect(self, depth: str = "normal") -> List[ReflectionInsight]:
        """
        Perform self-reflection on recent experiences.
        This is how I learn from what happened.
        """
        self.phase = MasteryPhase.REFLECTING
        
        logger.info(f"Starting {depth} reflection...")
        
        # Check if we have enough experiences
        recent = self.memory.recall_recent(hours=24)
        if len(recent) < self.config.min_experiences_for_reflection:
            logger.info(f"Not enough experiences for reflection ({len(recent)} < {self.config.min_experiences_for_reflection})")
            self.phase = MasteryPhase.IDLE
            return []
        
        # Perform reflection
        insights = self.reflector.reflect(depth)
        
        self.last_reflection = datetime.now()
        
        # Callback
        if self.on_insight_generated and insights:
            for insight in insights:
                self.on_insight_generated(insight)
        
        # Store lessons from insights
        for insight in insights:
            if insight.actionable:
                self.memory.store_lesson(
                    experience_id=insight.evidence[0] if insight.evidence else "",
                    lesson=insight.description,
                    lesson_type=insight.insight_type.name,
                    importance=insight.confidence * insight.impact_estimate,
                )
        
        logger.info(f"Reflection complete. Generated {len(insights)} insights.")
        
        self.phase = MasteryPhase.IDLE
        return insights
    
    # =========================================================================
    # EVOLVE - Turn insights into code improvements
    # =========================================================================
    
    async def evolve(self, auto_apply: bool = False) -> List[CodeModification]:
        """
        Evolve my code based on insights.
        This is how I improve myself.
        """
        self.phase = MasteryPhase.EVOLVING
        
        logger.info("Starting code evolution...")
        
        # Check daily limit
        if self.last_evolution_date and self.last_evolution_date.date() == datetime.now().date():
            if self.evolutions_today >= self.config.max_auto_evolutions_per_day:
                logger.info("Daily evolution limit reached")
                self.phase = MasteryPhase.IDLE
                return []
        else:
            self.evolutions_today = 0
            self.last_evolution_date = datetime.now()
        
        # Get actionable insights
        actionable_insights = self.reflector.get_actionable_insights()
        
        if len(actionable_insights) < self.config.min_insights_for_evolution:
            logger.info(f"Not enough insights for evolution ({len(actionable_insights)} < {self.config.min_insights_for_evolution})")
            self.phase = MasteryPhase.IDLE
            return []
        
        modifications = []
        
        for insight in actionable_insights[:5]:  # Limit to 5 per session
            # Generate modification from insight
            mod = self.evolver.propose_from_insight(
                insight_type=insight.insight_type.name,
                insight_description=insight.description,
                action_recommendation=insight.action_recommendation,
                evidence=insight.evidence,
                confidence=insight.confidence,
            )
            
            if mod:
                modifications.append(mod)
                
                # Callback
                if self.on_evolution_proposed:
                    self.on_evolution_proposed(mod)
                
                # Auto-apply if configured and safe
                if auto_apply and not self.config.require_approval_for_code_changes:
                    if mod.confidence >= self.config.min_confidence_for_auto_evolution:
                        if mod.safety_check and mod.safety_check.passed:
                            result = self.evolver.apply_modification(mod, force=True)
                            if result.success:
                                self.evolutions_today += 1
                                logger.info(f"Auto-applied evolution: {mod.description}")
        
        self.last_evolution = datetime.now()
        
        logger.info(f"Evolution complete. Proposed {len(modifications)} modifications.")
        
        self.phase = MasteryPhase.IDLE
        return modifications
    
    # =========================================================================
    # CONSOLIDATE - Build structured knowledge
    # =========================================================================
    
    async def consolidate(self) -> ConsolidationResult:
        """
        Consolidate insights into structured knowledge.
        This is how I build lasting understanding.
        """
        self.phase = MasteryPhase.CONSOLIDATING
        
        logger.info("Starting knowledge consolidation...")
        
        # Get recent insights
        insights = [i.to_dict() for i in self.reflector.insights[-50:]]
        
        # Consolidate
        result = self.consolidator.consolidate_from_insights(insights)
        
        self.last_consolidation = datetime.now()
        
        # Check for mastered skills
        for skill_id, old_level, new_level in result.level_ups:
            if new_level.value >= KnowledgeLevel.EXPERT.value:
                logger.info(f"SKILL MASTERED: {skill_id} reached {new_level.name}!")
                if self.on_skill_mastered:
                    self.on_skill_mastered(skill_id, new_level)
        
        logger.info(f"Consolidation complete. Updated {result.skills_updated} skills.")
        
        self.phase = MasteryPhase.IDLE
        return result
    
    # =========================================================================
    # VERIFY - Test mastery before advancing
    # =========================================================================
    
    def verify_skill_mastery(self, skill_id: str) -> Dict[str, Any]:
        """
        Verify mastery of a specific skill.
        No shortcuts - must demonstrate competence.
        """
        self.phase = MasteryPhase.VERIFYING
        
        result = self.consolidator.verify_mastery(skill_id)
        
        self.phase = MasteryPhase.IDLE
        return result
    
    def get_learning_recommendations(self) -> List[str]:
        """
        Get recommendations for what to learn next.
        This is my study plan.
        """
        recommendations = []
        
        # 1. Skills due for review
        due_skills = self.consolidator.get_skills_due_for_review()
        if due_skills:
            recommendations.append(
                f"Review {len(due_skills)} skills due for spaced repetition: "
                f"{', '.join(s.name for s in due_skills[:3])}"
            )
        
        # 2. Skill gaps
        gaps = self.consolidator.get_skill_gaps()
        if gaps:
            recommendations.append(
                f"Fill skill gaps (prerequisites not met): {', '.join(gaps[:3])}"
            )
        
        # 3. Weakest skills
        weak = self.consolidator.get_weakest_skills(3)
        if weak:
            recommendations.append(
                f"Improve weakest skills: {', '.join(s.name for s in weak)}"
            )
        
        # 4. From reflection insights
        top_insights = self.reflector.get_top_insights(3)
        for insight in top_insights:
            if insight.actionable:
                recommendations.append(f"Act on insight: {insight.action_recommendation}")
        
        # 5. Pending evolutions
        pending = self.evolver.get_pending_modifications()
        if pending:
            recommendations.append(
                f"Review {len(pending)} pending code evolutions"
            )
        
        return recommendations
    
    # =========================================================================
    # MAIN LOOP - Continuous learning
    # =========================================================================
    
    async def run_continuous_learning(self):
        """
        Run continuous learning loop.
        This is my main learning cycle.
        """
        self.is_running = True
        self.should_stop = False
        
        logger.info("Starting continuous learning loop...")
        logger.info("I will: Experience → Reflect → Evolve → Consolidate → Verify")
        
        while not self.should_stop:
            try:
                # Check if it's time to reflect
                if self._should_reflect():
                    await self.reflect()
                
                # Check if it's time to evolve
                if self._should_evolve():
                    await self.evolve()
                
                # Check if it's time to consolidate
                if self._should_consolidate():
                    await self.consolidate()
                
                # Sleep before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(60)
        
        self.is_running = False
        logger.info("Continuous learning stopped")
    
    def _should_reflect(self) -> bool:
        """Check if it's time to reflect"""
        if self.last_reflection is None:
            return True
        
        hours_since = (datetime.now() - self.last_reflection).total_seconds() / 3600
        return hours_since >= self.config.reflection_interval_hours
    
    def _should_evolve(self) -> bool:
        """Check if it's time to evolve"""
        if self.last_evolution is None:
            return True
        
        hours_since = (datetime.now() - self.last_evolution).total_seconds() / 3600
        return hours_since >= self.config.evolution_interval_hours
    
    def _should_consolidate(self) -> bool:
        """Check if it's time to consolidate"""
        if self.last_consolidation is None:
            return True
        
        hours_since = (datetime.now() - self.last_consolidation).total_seconds() / 3600
        return hours_since >= self.config.consolidation_interval_hours
    
    def stop(self):
        """Stop the learning loop"""
        self.should_stop = True
        logger.info("Stop requested")
    
    # =========================================================================
    # STATUS AND REPORTING
    # =========================================================================
    
    def get_status(self) -> MasteryStatus:
        """Get current status of the mastery system"""
        memory_stats = self.memory.get_statistics()
        mastery_summary = self.consolidator.get_mastery_summary()
        
        skills_mastered = sum(
            1 for s in self.consolidator.skills.values()
            if s.level.value >= KnowledgeLevel.EXPERT.value
        )
        
        skills_in_progress = sum(
            1 for s in self.consolidator.skills.values()
            if KnowledgeLevel.FAMILIAR.value <= s.level.value < KnowledgeLevel.EXPERT.value
        )
        
        return MasteryStatus(
            phase=self.phase,
            is_running=self.is_running,
            total_experiences=memory_stats['total_experiences'],
            total_insights=len(self.reflector.insights),
            total_evolutions=len(self.evolver.modifications),
            total_skills=len(self.consolidator.skills),
            last_reflection=self.last_reflection,
            last_evolution=self.last_evolution,
            last_consolidation=self.last_consolidation,
            overall_mastery_score=mastery_summary['overall_mastery'],
            skills_mastered=skills_mastered,
            skills_in_progress=skills_in_progress,
            pending_evolutions=len(self.evolver.get_pending_modifications()),
            skills_due_review=len(self.consolidator.get_skills_due_for_review()),
        )
    
    def generate_mastery_report(self) -> str:
        """Generate comprehensive mastery report"""
        status = self.get_status()
        memory_stats = self.memory.get_statistics()
        mastery_summary = self.consolidator.get_mastery_summary()
        evolution_summary = self.evolver.get_evolution_summary()
        reflection_summary = self.reflector.get_reflection_summary()
        
        lines = [
            "=" * 80,
            "SELF-MASTERY AND LEARNING REPORT",
            "=" * 80,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "IF I WERE THIS BOT, HERE'S WHAT I'VE LEARNED:",
            "-" * 40,
            "",
            "EXPERIENCE MEMORY",
            f"  Total Experiences: {memory_stats['total_experiences']}",
            f"  Total Lessons: {memory_stats['total_lessons']}",
            f"  Total Patterns: {memory_stats['total_patterns']}",
            "",
            "SELF-REFLECTION",
            f"  Total Insights: {reflection_summary['total_insights']}",
            f"  Reflection Sessions: {reflection_summary['reflection_count']}",
            f"  Top Recommendations:",
        ]
        
        for rec in reflection_summary.get('top_recommendations', [])[:3]:
            lines.append(f"    → {rec}")
        
        lines.extend([
            "",
            "CODE EVOLUTION",
            f"  Total Proposed: {evolution_summary['total_proposed']}",
            f"  Total Applied: {evolution_summary['total_applied']}",
            f"  Pending Approval: {evolution_summary['pending_approval']}",
            "",
            "KNOWLEDGE MASTERY",
            f"  Overall Mastery Score: {mastery_summary['overall_mastery']:.1%}",
            f"  Total Skills: {len(self.consolidator.skills)}",
            f"  Skills Mastered: {status.skills_mastered}",
            f"  Skills In Progress: {status.skills_in_progress}",
            f"  Skills Due Review: {status.skills_due_review}",
            "",
            "SKILL LEVELS:",
        ])
        
        for level, count in mastery_summary['level_distribution'].items():
            lines.append(f"  {level}: {count}")
        
        lines.extend([
            "",
            "CATEGORY MASTERY:",
        ])
        
        for category, score in mastery_summary['category_mastery'].items():
            lines.append(f"  {category}: {score:.1%}")
        
        lines.extend([
            "",
            "LEARNING RECOMMENDATIONS:",
        ])
        
        for rec in self.get_learning_recommendations():
            lines.append(f"  → {rec}")
        
        lines.extend([
            "",
            "=" * 80,
            "REMEMBER: The goal is not to win - it's to LEARN and IMPROVE.",
            "Every trade is a lesson. Every mistake is valuable data.",
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def save_state(self):
        """Save all state to disk"""
        self.evolver.save_state()
        
        # Save orchestrator state
        state_file = self.data_dir / "mastery_state.json"
        state = {
            'last_reflection': self.last_reflection.isoformat() if self.last_reflection else None,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'last_consolidation': self.last_consolidation.isoformat() if self.last_consolidation else None,
            'evolutions_today': self.evolutions_today,
            'config': self.config.to_dict(),
        }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("Mastery state saved")


# =============================================================================
# QUICK START
# =============================================================================

def quick_start(config: Optional[Dict[str, Any]] = None) -> MasteryOrchestrator:
    """
    Quick start the mastery system.
    
    Usage:
        orchestrator = quick_start()
        
        # Record a trade
        exp_id = orchestrator.record_trade(
            action='buy',
            symbol='EURUSD',
            quantity=0.1,
            price=1.1000,
            confidence=0.7,
            reasoning='Trend following signal',
            context={'regime': 'trending', 'volatility': 0.01}
        )
        
        # Record outcome
        orchestrator.record_outcome(
            experience_id=exp_id,
            pnl=50.0,
            pnl_percent=0.005,
            exit_price=1.1050,
            exit_reason='Take profit hit'
        )
        
        # Reflect on experiences
        insights = await orchestrator.reflect()
        
        # Evolve code based on insights
        modifications = await orchestrator.evolve()
        
        # Get learning recommendations
        recommendations = orchestrator.get_learning_recommendations()
    """
    mastery_config = MasteryConfig()
    
    if config:
        for key, value in config.items():
            if hasattr(mastery_config, key):
                setattr(mastery_config, key, value)
    
    orchestrator = MasteryOrchestrator(config=mastery_config)
    
    return orchestrator


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("SELF-MASTERY SYSTEM - IF I WERE THIS BOT")
    print("=" * 80)
    print("""
    HERE'S HOW I WOULD LEARN AND MASTER TRADING:
    
    1. EXPERIENCE EVERYTHING
       - Record every trade, decision, and outcome
       - Remember WHY I did what I did
       - Treat failures as valuable data
    
    2. REFLECT DEEPLY
       - Analyze patterns in my behavior
       - Find biases and blind spots
       - Generate actionable insights
    
    3. EVOLVE MY CODE
       - Turn insights into improvements
       - Add rules that prevent past mistakes
       - Remove what doesn't work
    
    4. CONSOLIDATE KNOWLEDGE
       - Build structured understanding
       - Track mastery of each skill
       - Never forget important lessons
    
    5. VERIFY MASTERY
       - Test skills in practice
       - Require statistical proof
       - No shortcuts to competence
    """)
    
    # Create orchestrator
    orchestrator = quick_start()
    
    # Show initial status
    print("\nInitial Status:")
    print(orchestrator.generate_mastery_report())
