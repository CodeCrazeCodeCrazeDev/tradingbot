"""
Self-Mastery System Demo

Demonstrates how the bot learns, reflects, evolves, and masters trading.

IF I WERE THIS BOT, HERE'S WHAT I WOULD DO:
1. Experience everything - record all trades and decisions
2. Reflect deeply - analyze patterns and find insights
3. Evolve my code - turn learning into improvements
4. Consolidate knowledge - build structured mastery
5. Verify before advancing - prove competence
"""

import asyncio
import logging
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.self_mastery import (
    MasteryOrchestrator,
    MasteryConfig,
    quick_start,
)
from trading_bot.self_mastery.experience_memory import (
    ExperienceMemory,
    ExperienceType,
    DecisionContext,
    OutcomeQuality,
)
from trading_bot.self_mastery.self_reflection import (
    SelfReflector,
    InsightType,
)
from trading_bot.self_mastery.code_evolver import (
    CodeEvolver,
    EvolutionType,
)
from trading_bot.self_mastery.knowledge_consolidator import (
    KnowledgeConsolidator,
    KnowledgeLevel,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subheader(title: str):
    """Print a formatted subheader"""
    print(f"\n--- {title} ---")


# =============================================================================
# DEMO 1: Experience Memory
# =============================================================================

def demo_experience_memory():
    """Demonstrate the experience memory system"""
    print_header("DEMO 1: EXPERIENCE MEMORY")
    print("""
    IF I WERE THIS BOT, I WOULD REMEMBER EVERYTHING:
    - Every trade I made and why
    - Every decision context (market state, signals, confidence)
    - Every outcome (profit, loss, near-miss)
    - Every mistake and what caused it
    """)
    
    memory = ExperienceMemory(data_dir="demo_data/memory")
    
    # Simulate some trading experiences
    print_subheader("Recording Trading Experiences")
    
    experiences = []
    for i in range(10):
        # Create decision context
        context = DecisionContext(
            timestamp=datetime.now() - timedelta(hours=i),
            price=100.0 + random.uniform(-5, 5),
            volume=1000 + random.uniform(-200, 200),
            volatility=0.01 + random.uniform(0, 0.02),
            spread=0.0001,
            regime=random.choice(['trending', 'ranging', 'volatile']),
            trend=random.choice(['up', 'down', 'sideways']),
            confidence=random.uniform(0.3, 0.9),
            risk_level=random.uniform(0.1, 0.5),
            current_position=random.uniform(-1, 1),
            unrealized_pnl=random.uniform(-100, 100),
            drawdown=random.uniform(0, 0.1),
        )
        
        # Create experience
        exp = memory.create_experience(
            experience_type=ExperienceType.TRADE_EXECUTED,
            action=random.choice(['buy', 'sell']),
            symbol='EURUSD',
            quantity=0.1,
            context=context,
            reasoning=f"Signal {i+1}: {'Bullish' if random.random() > 0.5 else 'Bearish'} pattern detected",
            confidence=context.confidence,
            tags=['demo', context.regime],
            importance=random.uniform(0.3, 0.9),
        )
        
        exp_id = memory.remember(exp)
        experiences.append(exp_id)
        print(f"  Recorded experience {i+1}: {exp.action} @ {context.price:.2f} (confidence: {context.confidence:.1%})")
    
    # Recall similar experiences
    print_subheader("Recalling Similar Experiences")
    current_context = DecisionContext(
        timestamp=datetime.now(),
        price=102.0,
        volume=1100,
        volatility=0.015,
        spread=0.0001,
        regime='trending',
        trend='up',
        confidence=0.7,
        risk_level=0.3,
        current_position=0,
        unrealized_pnl=0,
        drawdown=0.02,
    )
    
    similar = memory.recall_similar(current_context, limit=3)
    print(f"  Found {len(similar)} similar experiences")
    for exp in similar:
        print(f"    - {exp.action} @ {exp.context.price:.2f} in {exp.context.regime} regime")
    
    # Store a lesson
    print_subheader("Storing Lessons")
    memory.store_lesson(
        experience_id=experiences[0],
        lesson="Don't trade during high volatility news events",
        lesson_type="RISK_MANAGEMENT",
        importance=0.9
    )
    print("  Stored lesson: Don't trade during high volatility news events")
    
    # Get statistics
    print_subheader("Memory Statistics")
    stats = memory.get_statistics()
    print(f"  Total experiences: {stats['total_experiences']}")
    print(f"  Total lessons: {stats['total_lessons']}")
    print(f"  Average importance: {stats['average_importance']:.2f}")
    
    return memory


# =============================================================================
# DEMO 2: Self-Reflection
# =============================================================================

def demo_self_reflection(memory: ExperienceMemory):
    """Demonstrate the self-reflection system"""
    print_header("DEMO 2: SELF-REFLECTION")
    print("""
    IF I WERE THIS BOT, I WOULD CONSTANTLY ASK MYSELF:
    - Why did that trade work/fail?
    - What patterns am I missing?
    - What am I doing wrong repeatedly?
    - How can I improve my decision-making?
    """)
    
    reflector = SelfReflector(memory, data_dir="demo_data/reflection")
    
    # Add some outcomes to experiences for reflection
    print_subheader("Adding Outcomes to Experiences")
    from trading_bot.self_mastery.experience_memory import OutcomeAnalysis
    
    recent = memory.recall_recent(hours=24)
    for i, exp in enumerate(recent[:5]):
        pnl = random.uniform(-50, 100)
        outcome = OutcomeAnalysis(
            decision_time=exp.context.timestamp,
            outcome_time=datetime.now(),
            duration_seconds=random.uniform(60, 3600),
            pnl=pnl,
            pnl_percent=pnl / 10000,
            max_favorable_excursion=abs(pnl) * 1.5,
            max_adverse_excursion=abs(pnl) * 0.5,
            quality=OutcomeQuality.GOOD if pnl > 0 else OutcomeQuality.POOR,
            price_at_decision=exp.context.price,
            price_at_outcome=exp.context.price + pnl / 100,
            price_change_percent=pnl / 10000,
            prediction_correct=pnl > 0,
            prediction_confidence=exp.confidence_at_decision,
            risk_reward_ratio=abs(pnl) / 50 if pnl != 0 else 0,
            sharpe_contribution=0,
        )
        memory.update_outcome(exp.experience_id, outcome)
        print(f"  Added outcome to experience {i+1}: PnL = ${pnl:.2f}")
    
    # Perform reflection
    print_subheader("Performing Self-Reflection")
    insights = reflector.reflect(depth="normal")
    
    print(f"\n  Generated {len(insights)} insights:")
    for insight in insights[:5]:
        print(f"\n  [{insight.insight_type.name}]")
        print(f"    Description: {insight.description[:80]}...")
        print(f"    Confidence: {insight.confidence:.1%}")
        print(f"    Actionable: {insight.actionable}")
        if insight.actionable:
            print(f"    Recommendation: {insight.action_recommendation[:60]}...")
    
    # Get reflection summary
    print_subheader("Reflection Summary")
    summary = reflector.get_reflection_summary()
    print(f"  Total insights: {summary['total_insights']}")
    print(f"  Reflection sessions: {summary['reflection_count']}")
    
    return reflector


# =============================================================================
# DEMO 3: Code Evolution
# =============================================================================

def demo_code_evolution(reflector: SelfReflector):
    """Demonstrate the code evolution system"""
    print_header("DEMO 3: CODE EVOLUTION")
    print("""
    IF I WERE THIS BOT, I WOULD REWRITE MYSELF TO BE BETTER:
    - Turn insights into code changes
    - Add rules that prevent past mistakes
    - Optimize parameters based on data
    - Remove strategies that don't work
    """)
    
    evolver = CodeEvolver(data_dir="demo_data/evolution")
    
    # Propose parameter change
    print_subheader("Proposing Parameter Change")
    param_mod = evolver.propose_parameter_change(
        parameter_name="max_daily_trades",
        current_value=100,
        new_value=10,
        target_file="trading_bot/risk/risk_manager.py",
        reason="Overtrading detected - limiting to prevent losses",
        confidence=0.75
    )
    print(f"  Proposed: {param_mod.description}")
    print(f"  Safety check passed: {param_mod.safety_check.passed}")
    print(f"  Safety level: {param_mod.safety_check.safety_level.name}")
    
    # Propose filter addition
    print_subheader("Proposing Filter Addition")
    filter_mod = evolver.propose_filter_addition(
        filter_name="high_volatility",
        condition="context.volatility > 0.03",
        filter_logic="# Filter out high volatility conditions",
        description="Avoid trading during extreme volatility",
        target_file="trading_bot/self_mastery/learned_filters.py",
        reason="Losses correlated with high volatility periods",
        confidence=0.8
    )
    print(f"  Proposed: {filter_mod.description}")
    print(f"  Safety check passed: {filter_mod.safety_check.passed}")
    
    # Propose from insight
    print_subheader("Proposing Evolution from Insight")
    actionable = reflector.get_actionable_insights()
    if actionable:
        insight = actionable[0]
        insight_mod = evolver.propose_from_insight(
            insight_type=insight.insight_type.name,
            insight_description=insight.description,
            action_recommendation=insight.action_recommendation,
            evidence=insight.evidence,
            confidence=insight.confidence
        )
        if insight_mod:
            print(f"  Generated modification from insight: {insight_mod.description}")
    
    # Get evolution summary
    print_subheader("Evolution Summary")
    summary = evolver.get_evolution_summary()
    print(f"  Total proposed: {summary['total_proposed']}")
    print(f"  Pending approval: {summary['pending_approval']}")
    
    return evolver


# =============================================================================
# DEMO 4: Knowledge Consolidation
# =============================================================================

def demo_knowledge_consolidation(reflector: SelfReflector):
    """Demonstrate the knowledge consolidation system"""
    print_header("DEMO 4: KNOWLEDGE CONSOLIDATION")
    print("""
    IF I WERE THIS BOT, I WOULD BUILD MASTERY:
    - Turn insights into structured skills
    - Track mastery level for each skill
    - Use spaced repetition to reinforce learning
    - Never forget critical lessons
    """)
    
    consolidator = KnowledgeConsolidator(data_dir="demo_data/knowledge")
    
    # Show initial skills
    print_subheader("Core Trading Skills")
    for skill_id, skill in list(consolidator.skills.items())[:6]:
        print(f"  {skill.name}: {skill.level.name} ({skill.mastery_score:.1%})")
    
    # Consolidate from insights
    print_subheader("Consolidating Knowledge from Insights")
    insights = [i.to_dict() for i in reflector.insights[:10]]
    result = consolidator.consolidate_from_insights(insights)
    
    print(f"  Insights processed: {result.insights_processed}")
    print(f"  Skills updated: {result.skills_updated}")
    print(f"  Skills created: {result.skills_created}")
    print(f"  Level ups: {len(result.level_ups)}")
    
    # Record skill application
    print_subheader("Recording Skill Applications")
    consolidator.record_application(
        skill_id="entry_timing",
        success=True,
        context={'action': 'buy', 'symbol': 'EURUSD'},
        outcome="Profitable trade"
    )
    print("  Recorded successful application of 'entry_timing'")
    
    consolidator.record_application(
        skill_id="risk_per_trade",
        success=False,
        context={'action': 'buy', 'symbol': 'EURUSD'},
        outcome="Position too large"
    )
    print("  Recorded failed application of 'risk_per_trade'")
    
    # Get mastery summary
    print_subheader("Mastery Summary")
    summary = consolidator.get_mastery_summary()
    print(f"  Overall mastery: {summary['overall_mastery']:.1%}")
    print(f"  Total skills: {summary['total_skills']}")
    print(f"  Skills due review: {summary['skills_due_review']}")
    print(f"  Weakest skills: {', '.join(summary['weakest_skills'])}")
    print(f"  Strongest skills: {', '.join(summary['strongest_skills'])}")
    
    # Verify mastery
    print_subheader("Verifying Skill Mastery")
    verification = consolidator.verify_mastery("entry_timing")
    print(f"  entry_timing verified: {verification['verified']}")
    if not verification['verified']:
        print(f"    Reason: {verification.get('reason', 'N/A')}")
    
    return consolidator


# =============================================================================
# DEMO 5: Full Mastery Orchestrator
# =============================================================================

async def demo_mastery_orchestrator():
    """Demonstrate the full mastery orchestrator"""
    print_header("DEMO 5: MASTERY ORCHESTRATOR")
    print("""
    THE COMPLETE LEARNING CYCLE:
    1. Experience → 2. Reflect → 3. Evolve → 4. Consolidate → 5. Verify
    """)
    
    # Create orchestrator
    config = MasteryConfig(
        reflection_interval_hours=0.1,  # Quick for demo
        min_experiences_for_reflection=3,
        min_insights_for_evolution=2,
    )
    orchestrator = MasteryOrchestrator(config=config, data_dir="demo_data/mastery")
    
    # Simulate trading
    print_subheader("Simulating Trading Activity")
    
    for i in range(5):
        # Record a trade
        exp_id = orchestrator.record_trade(
            action=random.choice(['buy', 'sell']),
            symbol='EURUSD',
            quantity=0.1,
            price=1.1000 + random.uniform(-0.01, 0.01),
            confidence=random.uniform(0.5, 0.9),
            reasoning=f"Signal {i+1}: Pattern detected",
            context={
                'regime': random.choice(['trending', 'ranging']),
                'volatility': random.uniform(0.01, 0.03),
                'trend': random.choice(['up', 'down']),
                'drawdown': random.uniform(0, 0.05),
            }
        )
        
        # Simulate outcome
        pnl = random.uniform(-30, 50)
        orchestrator.record_outcome(
            experience_id=exp_id,
            pnl=pnl,
            pnl_percent=pnl / 10000,
            exit_price=1.1000 + pnl / 10000,
            exit_reason='Take profit' if pnl > 0 else 'Stop loss'
        )
        
        print(f"  Trade {i+1}: PnL = ${pnl:.2f}")
    
    # Reflect
    print_subheader("Reflecting on Experiences")
    insights = await orchestrator.reflect(depth="quick")
    print(f"  Generated {len(insights)} insights")
    
    # Evolve
    print_subheader("Evolving Code")
    modifications = await orchestrator.evolve()
    print(f"  Proposed {len(modifications)} modifications")
    
    # Consolidate
    print_subheader("Consolidating Knowledge")
    result = await orchestrator.consolidate()
    print(f"  Updated {result.skills_updated} skills")
    
    # Get recommendations
    print_subheader("Learning Recommendations")
    recommendations = orchestrator.get_learning_recommendations()
    for rec in recommendations[:5]:
        print(f"  → {rec}")
    
    # Get status
    print_subheader("System Status")
    status = orchestrator.get_status()
    print(f"  Total experiences: {status.total_experiences}")
    print(f"  Total insights: {status.total_insights}")
    print(f"  Overall mastery: {status.overall_mastery_score:.1%}")
    print(f"  Skills mastered: {status.skills_mastered}")
    
    # Generate report
    print_subheader("Mastery Report")
    report = orchestrator.generate_mastery_report()
    print(report)
    
    return orchestrator


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all demos"""
    print("=" * 80)
    print("SELF-MASTERY SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("""
    IF I WERE THIS BOT, HERE'S HOW I WOULD LEARN AND MASTER TRADING:
    
    1. EXPERIENCE EVERYTHING - Record every trade and decision
    2. REFLECT DEEPLY - Analyze patterns and find insights
    3. EVOLVE MY CODE - Turn learning into improvements
    4. CONSOLIDATE KNOWLEDGE - Build structured mastery
    5. VERIFY MASTERY - Prove competence before advancing
    
    Let's see each component in action...
    """)
    
    # Run demos
    memory = demo_experience_memory()
    reflector = demo_self_reflection(memory)
    evolver = demo_code_evolution(reflector)
    consolidator = demo_knowledge_consolidation(reflector)
    orchestrator = await demo_mastery_orchestrator()
    
    # Final summary
    print_header("DEMONSTRATION COMPLETE")
    print("""
    KEY TAKEAWAYS:
    
    1. EXPERIENCE MEMORY
       - Remembers every trade and decision
       - Stores context for understanding WHY
       - Extracts and stores lessons
    
    2. SELF-REFLECTION
       - Analyzes patterns in behavior
       - Identifies biases and mistakes
       - Generates actionable insights
    
    3. CODE EVOLUTION
       - Turns insights into code changes
       - Adds rules to prevent mistakes
       - Safe self-modification with backups
    
    4. KNOWLEDGE CONSOLIDATION
       - Builds structured skill mastery
       - Tracks progress for each skill
       - Uses spaced repetition
    
    5. MASTERY ORCHESTRATOR
       - Coordinates all systems
       - Runs continuous learning
       - Generates recommendations
    
    REMEMBER: The goal is not to win - it's to LEARN and IMPROVE.
    Every trade is a lesson. Every mistake is valuable data.
    """)


if __name__ == "__main__":
    asyncio.run(main())
