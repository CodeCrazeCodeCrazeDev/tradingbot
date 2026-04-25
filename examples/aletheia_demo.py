"""
Aletheia Integration Example and Demo

Demonstrates how to use the Aletheia autonomous research system
with AlphaAlgo governance integration.
"""

import asyncio
import logging

# Import Aletheia components
from trading_bot.aletheia_autonomous import (
    AletheiaOrchestrator,
    StrategyGenerator,
    StrategyVerifier,
    StrategyReviser,
    AutonomousResearchFramework,
    ResearchPriority,
    AutonomyLevel,
    AletheiaGovernanceIntegration,
    HumanAIInterface,
    InteractionMode,
    AletheiaPrinciples,
    ToolIntegrationSystem,
    AletheiaTestFramework
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_research():
    """Demo: Basic autonomous research cycle"""
    logger.info("=" * 60)
    logger.info("DEMO 1: Basic Autonomous Research Cycle")
    logger.info("=" * 60)
    
    # Initialize subagents
    generator = StrategyGenerator()
    verifier = StrategyVerifier()
    reviser = StrategyReviser()
    
    # Create orchestrator
    orchestrator = AletheiaOrchestrator(
        generator=generator,
        verifier=verifier,
        reviser=reviser,
        max_iterations=3,
        min_confidence_threshold=0.85
    )
    
    # Conduct research
    hypothesis = await orchestrator.research_strategy(
        research_prompt="Create a momentum strategy for trending forex markets",
        market_context={
            "trend": "strong_up",
            "volatility": "medium",
            "regime": "trending",
            "data_quality": "high"
        },
        constraints={
            "max_risk_per_trade": 2.0,
            "max_daily_loss": 3.0,
            "preferred_timeframes": ["H1", "H4"]
        }
    )
    
    # Display results
    logger.info(f"\nStrategy Generated: {hypothesis.title}")
    logger.info(f"Description: {hypothesis.description}")
    logger.info(f"Rationale: {hypothesis.rationale}")
    logger.info(f"\nConfidence Score: {hypothesis.confidence_score:.1%}")
    logger.info(f"Verification Status: {hypothesis.verification_status}")
    logger.info(f"Revisions Made: {hypothesis.revision_count}")
    
    logger.info(f"\nEntry Rules ({len(hypothesis.entry_rules)}):")
    for i, rule in enumerate(hypothesis.entry_rules[:3], 1):
        logger.info(f"  {i}. {rule}")
    
    logger.info(f"\nExit Rules ({len(hypothesis.exit_rules)}):")
    for i, rule in enumerate(hypothesis.exit_rules[:3], 1):
        logger.info(f"  {i}. {rule}")
    
    logger.info(f"\nRisk Parameters:")
    for key, value in hypothesis.risk_parameters.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"\nExpected Performance:")
    for key, value in hypothesis.expected_performance.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2f}")
        else:
            logger.info(f"  {key}: {value}")
    
    return hypothesis


async def demo_batch_research():
    """Demo: Batch research multiple strategies"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 2: Batch Research Multiple Strategies")
    logger.info("=" * 60)
    
    generator = StrategyGenerator()
    verifier = StrategyVerifier()
    reviser = StrategyReviser()
    
    orchestrator = AletheiaOrchestrator(
        generator=generator,
        verifier=verifier,
        reviser=reviser
    )
    
    # Multiple research prompts
    prompts = [
        "Create a mean reversion strategy for ranging markets",
        "Create a breakout strategy for volatile markets",
        "Create a sentiment-based strategy for news-driven moves"
    ]
    
    logger.info(f"Researching {len(prompts)} strategies in parallel...")
    
    hypotheses = await orchestrator.batch_research(
        research_prompts=prompts,
        parallel=True
    )
    
    logger.info(f"\nGenerated {len(hypotheses)} strategies:")
    for i, h in enumerate(hypotheses, 1):
        logger.info(f"\n{i}. {h.title}")
        logger.info(f"   Type: {h.description[:50]}...")
        logger.info(f"   Confidence: {h.confidence_score:.1%}")
        logger.info(f"   Status: {h.verification_status}")
    
    return hypotheses


async def demo_research_framework():
    """Demo: Full research framework with projects"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 3: Autonomous Research Framework")
    logger.info("=" * 60)
    
    # Initialize framework
    research_framework = AutonomousResearchFramework()
    
    # Create research project
    project = await research_framework.create_research_project(
        title="Q1 2026 Strategy Research",
        description="Research and develop strategies for Q1 2026 trading",
        research_prompts=[
            "Momentum strategy for tech stocks",
            "Mean reversion for forex majors",
            "Breakout strategy for crypto",
            "Statistical arbitrage for correlated pairs"
        ],
        priority=ResearchPriority.HIGH,
        autonomy_level=AutonomyLevel.LEVEL_C,
        market_context={
            "regime": "mixed",
            "volatility": "elevated",
            "trend": "neutral"
        },
        constraints={
            "max_risk_per_trade": 2.0,
            "max_portfolio_risk": 15.0
        },
        target_hypothesis_count=3
    )
    
    logger.info(f"Created research project: {project.title}")
    logger.info(f"Project ID: {project.project_id}")
    logger.info(f"Priority: {project.priority.value}")
    logger.info(f"Autonomy Level: {project.autonomy_level.value}")
    logger.info(f"Target Strategies: {project.target_hypothesis_count}")
    
    return project


async def demo_governance_integration():
    """Demo: Governance integration with AlphaAlgo"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 4: Governance Integration")
    logger.info("=" * 60)
    
    # Initialize systems
    research_framework = AutonomousResearchFramework()
    governance = AletheiaGovernanceIntegration(
        research_framework=research_framework,
        strict_mode=True
    )
    
    # Request approval for research project
    approval = await governance.create_governed_research_project(
        title="Governed Research Project",
        description="Research with full governance oversight",
        research_prompts=[
            "Conservative momentum strategy",
            "Low-risk mean reversion"
        ],
        autonomy_level=AutonomyLevel.LEVEL_C,
        requester="DemoUser"
    )
    
    logger.info(f"Governance approval requested: {approval['approval_id']}")
    logger.info(f"Project ID: {approval['project_id']}")
    logger.info(f"Status: {approval['status']}")
    
    # Show governance summary
    summary = governance.get_governance_summary()
    logger.info(f"\nGovernance Summary:")
    logger.info(f"  Pending Approvals: {summary['pending_approvals']['total']}")
    logger.info(f"  Policies - Strict Mode: {summary['policies']['strict_mode']}")
    logger.info(f"  Policies - Research Approval: {summary['policies']['require_research_approval']}")
    
    return governance


async def demo_human_ai_interface():
    """Demo: Human-AI collaboration interface"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 5: Human-AI Collaboration")
    logger.info("=" * 60)
    
    # Initialize systems
    research_framework = AutonomousResearchFramework()
    governance = AletheiaGovernanceIntegration(research_framework)
    interface = HumanAIInterface(
        research_framework=research_framework,
        governance_integration=governance,
        default_mode=InteractionMode.SUPERVISED
    )
    
    # First generate a strategy to review
    generator = StrategyGenerator()
    hypothesis = await generator.generate(
        prompt="Strategy for review",
        market_context={"trend": "up", "volatility": "medium"}
    )
    
    # Add to a project for tracking
    project = await research_framework.create_research_project(
        title="Review Demo",
        description="Demo project",
        research_prompts=["Test"],
        autonomy_level=AutonomyLevel.LEVEL_C
    )
    project.hypotheses.append(hypothesis)
    project.best_hypothesis = hypothesis
    
    # Present strategy for review
    presentation = await interface.present_strategy_for_review(
        hypothesis_id=hypothesis.hypothesis_id,
        presentation_format="detailed"
    )
    
    logger.info(f"Strategy presented for review: {presentation.title}")
    logger.info(f"Confidence: {presentation.confidence_score:.1%}")
    logger.info(f"Verification: {presentation.verification_status}")
    
    logger.info(f"\nSummary:\n{presentation.summary}")
    
    if presentation.warnings:
        logger.info(f"\nWarnings ({len(presentation.warnings)}):")
        for warning in presentation.warnings:
            logger.info(f"  - {warning}")
    
    if presentation.recommendations:
        logger.info(f"\nRecommendations ({len(presentation.recommendations)}):")
        for rec in presentation.recommendations:
            logger.info(f"  - {rec}")
    
    return interface


async def demo_principles():
    """Demo: Aletheia principles system"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 6: Aletheia Principles (200 Total)")
    logger.info("=" * 60)
    
    principles = AletheiaPrinciples()
    
    # Get summary
    summary = principles.get_principles_summary()
    logger.info(f"Total Principles: {summary['total_principles']}")
    
    logger.info("\nBy Category:")
    for category, count in summary['by_category'].items():
        logger.info(f"  {category}: {count} principles")
    
    logger.info("\nBy Priority:")
    for priority, count in summary['by_priority'].items():
        logger.info(f"  {priority.capitalize()}: {count} principles")
    
    # Show sample principles
    logger.info("\nSample Principles:")
    sample = [
        principles.get_principle("RM001"),
        principles.get_principle("VS001"),
        principles.get_principle("AD001"),
        principles.get_principle("HC001")
    ]
    
    for p in sample:
        if p:
            logger.info(f"\n  {p.id} ({p.category}):")
            logger.info(f"    Principle: {p.principle}")
            logger.info(f"    Priority: {p.priority}")
    
    return principles


async def demo_testing_framework():
    """Demo: Testing and validation"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 7: Testing Framework")
    logger.info("=" * 60)
    
    test_framework = AletheiaTestFramework()
    
    logger.info("Running comprehensive test suite...")
    logger.info("(This may take a moment)")
    
    results = await test_framework.run_all_tests()
    
    logger.info(f"\nTest Results:")
    logger.info(f"  Total Tests: {results['total_tests']}")
    logger.info(f"  Passed: {results['passed']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Pass Rate: {results['pass_rate']:.1%}")
    logger.info(f"  Duration: {results['duration_seconds']:.2f}s")
    
    if results['failed_tests']:
        logger.info(f"\nFailed Tests:")
        for test in results['failed_tests']:
            logger.info(f"  - {test}")
    
    return results


async def main():
    """Run all demos"""
    logger.info("\n" + "=" * 60)
    logger.info("ALETHEIA AUTONOMOUS RESEARCH SYSTEM")
    logger.info("Based on DeepMind's Aletheia: Towards Autonomous Mathematics Research")
    logger.info("=" * 60)
    
    try:
        # Run all demos
        await demo_basic_research()
        await demo_batch_research()
        await demo_research_framework()
        await demo_governance_integration()
        await demo_human_ai_interface()
        await demo_principles()
        await demo_testing_framework()
        
        logger.info("\n" + "=" * 60)
        logger.info("ALL DEMOS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
