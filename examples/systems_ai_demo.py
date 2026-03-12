"""
AlphaAlgo Systems AI Demo
=========================
Demonstrates the complete Systems AI architecture.

Run: python examples/systems_ai_demo.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.systems_ai import (
    # Core
    SystemsAIOrchestrator,
    SignalRequest,
    SystemConfig,
    SystemMode,
    create_systems_ai,
    quick_start,
    # Memory
    MemoryHierarchy,
    # Attribution
    DecisionAttributionEngine,
    SignalDirection,
    # Training
    TrainingFirstArchitecture,
    # Research
    ResearchAgent,
    HypothesisType,
    # Text-to-System
    TextToSystemLayer,
    # Governance
    GovernanceEngine,
    GovernanceLevel,
    ActionType,
    # Self-Improvement
    SelfImprovementLoop,
    # Advanced Features
    MarketCurriculumLearner,
    DifficultyLevel,
    PredictiveFeatureDecay,
    SyntheticStressSimulator,
    StressScenario,
    CrossDomainKnowledgeTransfer,
    KnowledgeDomain,
    MultiAgentDebateLayer,
    EntropyGuidedExplorer,
    RealTimeWhatIfSandbox,
    AdvancedFeaturesCoordinator,
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def demo_signal_generation():
    """Demo: Signal generation with full attribution."""
    print_section("1. SIGNAL GENERATION WITH ATTRIBUTION")
    
    # Create orchestrator
    orchestrator = create_systems_ai(mode="paper")
    await orchestrator.initialize()
    
    # Create signal request
    request = SignalRequest(
        request_id="demo_001",
        symbol="BTCUSDT",
        timestamp=datetime.utcnow(),
        features={
            "trend": 0.6,
            "momentum": 0.4,
            "volatility": 0.3,
            "mean_reversion": -0.2,
            "imbalance": 0.15,
        },
        risk_budget=0.02,
    )
    
    # Generate signal
    response = orchestrator.generate_signal(request)
    
    print(f"\nSignal ID: {response.signal_id}")
    print(f"Direction: {response.direction.value}")
    print(f"Confidence: {response.confidence:.2%}")
    print(f"Magnitude: {response.magnitude:.4f}")
    print(f"Regime: {response.regime_id}")
    print(f"Recommended Size: {response.recommended_size:.4f}")
    print(f"\nReasoning:")
    for reason in response.reasoning:
        print(f"  - {reason}")
    
    if response.warnings:
        print(f"\nWarnings:")
        for warning in response.warnings:
            print(f"  ⚠ {warning}")
    
    print(f"\nContributing Models:")
    for model in response.contributing_models:
        print(f"  - {model['model_id']}: weight={model['weight']:.2f}, conf={model['confidence']:.2f}")
    
    await orchestrator.shutdown()


async def demo_memory_hierarchy():
    """Demo: 3-tier memory system."""
    print_section("2. MEMORY HIERARCHY")
    
    memory = MemoryHierarchy({})
    
    # Store in short-term
    print("\n[Short-Term Memory]")
    memory.short_term.store_microstructure(
        symbol="BTCUSDT",
        imbalance=0.15,
        spread=0.0001,
        toxicity=0.3,
        timestamp=datetime.utcnow(),
    )
    print("  Stored: Microstructure data")
    
    # Store in mid-term
    print("\n[Mid-Term Memory]")
    memory.mid_term.store_regime(
        regime_id="trending_up",
        confidence=0.85,
        features={"trend": 0.6, "momentum": 0.4},
        timestamp=datetime.utcnow(),
    )
    print("  Stored: Regime classification")
    
    # Store in long-term
    print("\n[Long-Term Memory]")
    memory.long_term.store_event(
        event_type="flash_crash",
        severity="high",
        impact={"drawdown": -0.15, "recovery_hours": 4},
        timestamp=datetime.utcnow(),
    )
    print("  Stored: Market event")
    
    # Get statistics
    stats = memory.get_statistics()
    print(f"\nMemory Statistics:")
    print(f"  Short-term entries: {stats['short_term']['entries']}")
    print(f"  Mid-term entries: {stats['mid_term']['entries']}")
    print(f"  Long-term entries: {stats['long_term']['entries']}")


async def demo_text_to_system():
    """Demo: Natural language commands."""
    print_section("3. TEXT-TO-SYSTEM COMMANDS")
    
    layer = TextToSystemLayer()
    
    # Allowed commands
    allowed_commands = [
        "Analyze slippage for the last 7 days",
        "Find features that fail in volatile regime",
        "Show attribution for signal abc123",
        "Compare model performance across regimes",
        "Simulate alternative sizing with kelly",
    ]
    
    print("\n[Allowed Commands]")
    for cmd in allowed_commands:
        result = layer.process_command(cmd)
        status = "✓" if result.success else "✗"
        print(f"  {status} '{cmd[:50]}...'")
    
    # Forbidden commands
    forbidden_commands = [
        "Execute trade buy 100 BTCUSDT",
        "Override risk limit to 50%",
        "Deploy model to production",
        "Disable safety checks",
    ]
    
    print("\n[Forbidden Commands - BLOCKED]")
    for cmd in forbidden_commands:
        result = layer.process_command(cmd)
        status = "✗ BLOCKED" if not result.success else "⚠ ALLOWED"
        print(f"  {status}: '{cmd}'")


async def demo_governance():
    """Demo: Governance and approval gates."""
    print_section("4. GOVERNANCE & SAFETY")
    
    governance = GovernanceEngine()
    
    # Check permissions
    print("\n[Permission Checks]")
    
    checks = [
        ("research_agent", GovernanceLevel.G2_AGENT, ActionType.HYPOTHESIS_PROPOSAL),
        ("research_agent", GovernanceLevel.G2_AGENT, ActionType.MODEL_DEPLOYMENT),
        ("system", GovernanceLevel.G1_SYSTEM, ActionType.SIGNAL_GENERATION),
        ("human", GovernanceLevel.G0_HUMAN, ActionType.RISK_PARAMETER_CHANGE),
    ]
    
    for actor, level, action in checks:
        can_act, reason = governance.can_perform_action(actor, level, action)
        status = "✓ ALLOWED" if can_act else "✗ DENIED"
        print(f"  {status}: {actor} ({level.value}) -> {action.value}")
    
    # Safety boundaries
    print("\n[Safety Boundaries]")
    
    boundary_checks = [
        ("max_position_size", 0.05),  # 5% - OK
        ("max_position_size", 0.15),  # 15% - VIOLATION
        ("max_daily_loss", 0.03),     # 3% - OK
        ("max_daily_loss", 0.08),     # 8% - VIOLATION
    ]
    
    for boundary, value in boundary_checks:
        passed, msg = governance.check_boundary(boundary, value)
        status = "✓ OK" if passed else "✗ VIOLATION"
        print(f"  {status}: {boundary}={value:.2%}")


async def demo_research_agent():
    """Demo: Research agent scientific loop."""
    print_section("5. RESEARCH AGENT (SCIENTIFIC LOOP)")
    
    agent = ResearchAgent()
    
    # Propose hypothesis
    print("\n[Proposing Hypothesis]")
    hypothesis = agent.propose_hypothesis(
        hypothesis_type=HypothesisType.FEATURE,
        name="momentum_zscore_20",
        description="Z-score normalized momentum over 20 periods",
        rationale="Standardized momentum may improve regime detection",
        specification={
            "base_feature": "momentum",
            "transformation": "zscore",
            "window": 20,
        },
        tags=["momentum", "normalization"],
    )
    print(f"  Created: {hypothesis.name}")
    print(f"  Type: {hypothesis.hypothesis_type.value}")
    print(f"  Status: {hypothesis.status.value}")
    
    # Test hypothesis
    print("\n[Testing Hypothesis]")
    results = agent.test_hypothesis(
        hypothesis_id=hypothesis.hypothesis_id,
        start_date=datetime.utcnow() - timedelta(days=365),
        end_date=datetime.utcnow(),
    )
    
    for result in results:
        status_icon = "✓" if result.status.value == "passed" else "✗"
        print(f"  {status_icon} {result.validation_type}: {result.status.value}")
    
    # Check constraints
    print("\n[Agent Constraints - IMMUTABLE]")
    from trading_bot.systems_ai.research_agent import AgentConstraints
    print(f"  Cannot deploy live: {AgentConstraints.CANNOT_DEPLOY_LIVE}")
    print(f"  Cannot modify risk: {AgentConstraints.CANNOT_MODIFY_RISK}")
    print(f"  Cannot bypass governance: {AgentConstraints.CANNOT_BYPASS_GOVERNANCE}")


async def demo_self_improvement():
    """Demo: Self-improvement loop."""
    print_section("6. SELF-IMPROVEMENT LOOP")
    
    loop = SelfImprovementLoop()
    
    # Set baseline
    print("\n[Setting Baseline]")
    loop.set_baseline(
        feature_distributions={
            "momentum": {"mean": 0.0, "std": 1.0},
            "volatility": {"mean": 0.2, "std": 0.1},
        },
        performance_metrics={
            "sharpe_ratio": 1.5,
            "win_rate": 0.55,
            "avg_pnl": 0.001,
        },
    )
    print("  Baseline set for drift detection")
    
    # Label some outcomes
    print("\n[Labeling Outcomes]")
    for i in range(5):
        loop.label_outcome(
            signal_id=f"signal_{i}",
            direction_correct=i % 2 == 0,
            pnl=0.01 if i % 2 == 0 else -0.005,
            pnl_percent=0.01 if i % 2 == 0 else -0.005,
            regime_id="trending",
            volatility=0.2,
            liquidity=0.8,
            model_id="ensemble",
            model_version="1.0",
            feature_hash="abc123",
            slippage=0.0001,
            execution_quality=0.95,
        )
    print(f"  Labeled 5 outcomes")
    
    # Run detection
    print("\n[Running Detection Cycle]")
    results = loop.run_detection_cycle(
        current_distributions={
            "momentum": {"mean": 0.1, "std": 1.2},  # Slight drift
            "volatility": {"mean": 0.25, "std": 0.15},
        },
        current_performance={
            "sharpe_ratio": 1.2,  # Slight decay
            "win_rate": 0.52,
            "avg_pnl": 0.0008,
        },
    )
    
    print(f"  Drift detections: {len(results['drift_detections'])}")
    print(f"  Performance decay: {results['performance_decay']}")
    print(f"  Triggers generated: {len(results['triggers'])}")


async def demo_advanced_features():
    """Demo: Advanced features."""
    print_section("7. ADVANCED FEATURES")
    
    coordinator = AdvancedFeaturesCoordinator()
    
    # Curriculum Learning
    print("\n[Curriculum Learning]")
    progress = coordinator.curriculum.get_progress()
    print(f"  Current stage: {progress['current_stage']}/{progress['total_stages']}")
    print(f"  Difficulty: {progress['stage_details']['difficulty']}")
    
    # Feature Decay
    print("\n[Feature Decay Tracking]")
    coordinator.feature_decay.register_feature("momentum_20")
    coordinator.feature_decay.update_efficacy("momentum_20", 0.8)
    coordinator.feature_decay.update_efficacy("momentum_20", 0.75)
    report = coordinator.feature_decay.get_decay_report()
    print(f"  Total features: {report['total_features']}")
    print(f"  Avg efficacy: {report['avg_efficacy']:.2f}")
    
    # Stress Testing
    print("\n[Stress Simulation]")
    prices = [100 + i * 0.1 for i in range(100)]
    volumes = [1000] * 100
    
    def dummy_strategy(p, v):
        return [0.001] * (len(p) - 1)
    
    result = coordinator.stress_simulator.run_stress_test(
        scenario=StressScenario.FLASH_CRASH,
        prices=prices,
        volumes=volumes,
        strategy_func=dummy_strategy,
    )
    print(f"  Scenario: {result.scenario.value}")
    print(f"  Max drawdown: {result.max_drawdown:.2%}")
    print(f"  Survived: {result.survived}")
    
    # Multi-Agent Debate
    print("\n[Multi-Agent Debate]")
    debate = coordinator.debate_layer.conduct_debate({
        "momentum": 0.5,
        "trend": 0.3,
        "sentiment": 0.2,
        "volatility": 0.4,
        "fear": 0.3,
        "zscore": 1.5,
    })
    print(f"  Consensus: {debate.consensus_position}")
    print(f"  Confidence: {debate.consensus_confidence:.2%}")
    print(f"  Dissent: {debate.dissent_strength:.2%}")
    
    # What-If Sandbox
    print("\n[What-If Sandbox]")
    scenario_id = coordinator.whatif_sandbox.create_scenario(
        description="Test 2x position sizing",
        parameter_changes={"position_multiplier": 2.0},
    )
    print(f"  Created scenario: {scenario_id[:8]}...")


async def demo_full_system():
    """Demo: Full system integration."""
    print_section("8. FULL SYSTEM STATUS")
    
    orchestrator = create_systems_ai(mode="paper")
    await orchestrator.initialize()
    
    status = orchestrator.get_system_status()
    
    print(f"\nSystem Mode: {status['mode']}")
    print(f"Initialized: {status['initialized']}")
    print(f"\nMemory Stats:")
    for tier, stats in status['memory_stats'].items():
        print(f"  {tier}: {stats.get('entries', 0)} entries")
    
    print(f"\nPending Approvals: {status['pending_approvals']}")
    
    # Show architecture diagram excerpt
    print("\n[Architecture Diagram - Excerpt]")
    diagram = orchestrator.get_architecture_diagram()
    lines = diagram.split('\n')[:15]
    for line in lines:
        print(line)
    print("  ...")
    
    await orchestrator.shutdown()


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("       ALPHAALGO SYSTEMS AI - COMPREHENSIVE DEMO")
    print("       Intelligence from Architecture, Not Parameters")
    print("=" * 70)
    
    try:
        await demo_signal_generation()
        await demo_memory_hierarchy()
        await demo_text_to_system()
        await demo_governance()
        await demo_research_agent()
        await demo_self_improvement()
        await demo_advanced_features()
        await demo_full_system()
        
        print_section("DEMO COMPLETE")
        print("\nAll Systems AI components demonstrated successfully!")
        print("\nKey Takeaways:")
        print("  1. Signals include full attribution (features, models, regime)")
        print("  2. Memory is tiered (short/mid/long-term)")
        print("  3. Text commands are validated (forbidden patterns blocked)")
        print("  4. Governance enforces G0/G1/G2 hierarchy")
        print("  5. Research agents CANNOT deploy or trade")
        print("  6. Self-improvement is measured, reversible, auditable")
        print("  7. Advanced features enhance discovery safely")
        print("\nCore Constraint: Text → system action ALLOWED")
        print("                Text → live trading FORBIDDEN")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
