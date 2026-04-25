"""
Example Usage: Continuous Capability Discovery Engine

This example demonstrates how to use the ContinuousCapabilityDiscoveryEngine
to enable your trading system to continuously map its capability space,
detect missing capabilities, generate targeted innovations, and integrate
only those that produce robust, measurable improvements under real-world constraints.
"""

import asyncio
from datetime import datetime

from trading_bot.decision_governance import (
    ContinuousCapabilityDiscoveryEngine,
    CapabilityStatus,
    InnovationStage,
    ConstraintProfile,
    create_continuous_discovery_engine,
    DecisionMemory,
    OutcomeMemory,
    FailureMemory,
    ControlledEvolutionPlane,
)


async def example_basic_usage():
    """
    Example 1: Basic Usage - Create and start continuous monitoring
    """
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create with default configuration
    engine = create_continuous_discovery_engine()
    
    # Or create with custom constraints
    constraints = ConstraintProfile(
        max_drawdown_limit=0.10,  # 10% max drawdown
        min_sharpe_ratio=1.2,
        min_win_rate=0.55,
        risk_adjusted_return_threshold=0.002,  # 0.2% minimum improvement
    )
    
    engine = create_continuous_discovery_engine(
        constraint_profile=constraints,
        storage_path="my_discovery_state.json"
    )
    
    # Start continuous monitoring (runs discovery cycle every hour by default)
    await engine.start_continuous_monitoring()
    
    # Let it run for a bit...
    await asyncio.sleep(5)
    
    # Get current status
    status = engine.get_status()
    print(f"Monitoring active: {status['monitoring']['is_active']}")
    print(f"Capabilities mapped: {status['capability_space']['total_capabilities']}")
    print(f"Active gaps: {status['gaps']['active']}")
    
    # Stop monitoring
    await engine.stop_continuous_monitoring()
    print("Monitoring stopped")


async def example_with_trading_system():
    """
    Example 2: Integration with existing trading system
    """
    print("\n" + "=" * 60)
    print("Example 2: Integration with Trading System")
    print("=" * 60)
    
    # Assuming you have an existing trading system with memory components
    class MockTradingSystem:
        def __init__(self):
            self.decision_memory = DecisionMemory("decisions.db")
            self.outcome_memory = OutcomeMemory("outcomes.db")
            self.failure_memory = FailureMemory("failures.db")
            # ... other components
    
    trading_system = MockTradingSystem()
    
    # Create engine that automatically extracts memory systems from trading system
    engine = create_continuous_discovery_engine(
        trading_system=trading_system,
        storage_path="trading_discovery_state.json"
    )
    
    # The engine will now:
    # - Scan your trading system's actual components
    # - Use real performance data from outcome_memory
    # - Detect gaps based on failure patterns
    # - Validate innovations against actual trading results
    
    print("Engine created with trading system integration")
    print(f"Decision memory: {engine.decision_memory is not None}")
    print(f"Outcome memory: {engine.outcome_memory is not None}")
    print(f"Failure memory: {engine.failure_memory is not None}")


async def example_manual_discovery():
    """
    Example 3: Manual discovery cycle execution
    """
    print("\n" + "=" * 60)
    print("Example 3: Manual Discovery Cycle")
    print("=" * 60)
    
    engine = create_continuous_discovery_engine()
    
    # Run a single discovery cycle manually
    result = await engine._run_discovery_cycle()
    
    print(f"Discovery cycle completed at: {result['cycle_timestamp']}")
    print(f"Capabilities mapped: {result['capabilities_mapped']}")
    print(f"Gaps detected: {result['gaps_detected']}")
    print(f"New innovations: {result['new_innovations']}")
    print(f"Validations started: {result['validations_started']}")
    print(f"Cycle duration: {result['cycle_duration_seconds']:.2f}s")


async def example_gap_analysis():
    """
    Example 4: Analyzing detected capability gaps
    """
    print("\n" + "=" * 60)
    print("Example 4: Gap Analysis")
    print("=" * 60)
    
    engine = create_continuous_discovery_engine()
    
    # Run discovery to populate gaps
    await engine._run_discovery_cycle()
    
    # Get comprehensive report
    report = engine.get_discovery_report()
    
    print("\nActive Gaps:")
    for gap in report['active_gaps'][:5]:  # Show top 5
        print(f"  - {gap['id']}: {gap['description'][:50]}...")
        print(f"    Severity: {gap['severity']:.2f}, Impact: {gap['impact_score']:.2f}")
        print(f"    Days open: {gap['days_open']}")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")


async def example_integration_hooks():
    """
    Example 5: Using integration hooks for custom logic
    """
    print("\n" + "=" * 60)
    print("Example 5: Integration Hooks")
    print("=" * 60)
    
    engine = create_continuous_discovery_engine()
    
    # Add pre-integration hook
    def pre_integration_check(innovation):
        print(f"Pre-integration check for: {innovation.name}")
        # Add your custom validation logic here
        # Return False to block integration
        return True
    
    # Add post-integration hook
    def post_integration_action(innovation, record):
        print(f"Post-integration action for: {innovation.name}")
        print(f"  Improvements: {record['improvements']}")
        # Add your custom post-integration logic here
        # e.g., notify team, update documentation, etc.
    
    # Add rollback hook
    def rollback_action(innovation, reason):
        print(f"Rollback action for: {innovation.name}")
        print(f"  Reason: {reason}")
        # Add your custom rollback logic here
    
    # Register hooks
    engine.pre_integration_hooks.append(pre_integration_check)
    engine.post_integration_hooks.append(post_integration_action)
    engine.rollback_hooks.append(rollback_action)
    
    print("Integration hooks registered")


async def example_constraint_configuration():
    """
    Example 6: Configuring validation constraints
    """
    print("\n" + "=" * 60)
    print("Example 6: Constraint Configuration")
    print("=" * 60)
    
    # Conservative constraints for risk-averse trading
    conservative = ConstraintProfile(
        max_drawdown_limit=0.05,  # Very strict drawdown limit
        min_sharpe_ratio=1.5,
        min_win_rate=0.60,
        max_position_concentration=0.10,
        risk_adjusted_return_threshold=0.005,  # Require 0.5% improvement
        calibration_quality_min=0.8,
        robustness_score_min=0.8,
    )
    
    # Aggressive constraints for high-frequency trading
    aggressive = ConstraintProfile(
        max_drawdown_limit=0.20,
        min_sharpe_ratio=0.8,
        min_win_rate=0.45,
        max_position_concentration=0.30,
        max_latency_ms=10,  # Very strict latency
        risk_adjusted_return_threshold=0.0005,  # Accept smaller improvements
    )
    
    # Balanced constraints (default-like)
    balanced = ConstraintProfile(
        max_drawdown_limit=0.15,
        min_sharpe_ratio=1.0,
        min_win_rate=0.50,
        max_position_concentration=0.20,
        risk_adjusted_return_threshold=0.001,
    )
    
    print("Constraint profiles created:")
    print(f"  Conservative: {conservative.max_drawdown_limit:.1%} max drawdown")
    print(f"  Aggressive: {aggressive.max_drawdown_limit:.1%} max drawdown")
    print(f"  Balanced: {balanced.max_drawdown_limit:.1%} max drawdown")


async def example_rollback():
    """
    Example 7: Rolling back an integrated innovation
    """
    print("\n" + "=" * 60)
    print("Example 7: Rollback Example")
    print("=" * 60)
    
    engine = create_continuous_discovery_engine()
    
    # Simulate rolling back an innovation
    # In real usage, you'd get the innovation_id from integration_history
    innovation_id = "innov_20240101120000_1234"
    
    result = await engine.rollback_innovation(
        innovation_id=innovation_id,
        reason="Performance degradation detected in live trading"
    )
    
    if result['success']:
        print(f"Rollback successful: {result['innovation_id']}")
        print(f"Reason: {result['rollback_reason']}")
        print(f"Rolled back at: {result['rolled_back_at']}")
    else:
        print(f"Rollback failed: {result.get('error', 'Unknown error')}")


async def example_reporting():
    """
    Example 8: Generating discovery reports
    """
    print("\n" + "=" * 60)
    print("Example 8: Reporting")
    print("=" * 60)
    
    engine = create_continuous_discovery_engine()
    await engine._run_discovery_cycle()
    
    # Get status snapshot
    status = engine.get_status()
    
    print("\nSystem Status:")
    print(f"  Monitoring: {'Active' if status['monitoring']['is_active'] else 'Inactive'}")
    print(f"  Total Capabilities: {status['capability_space']['total_capabilities']}")
    print(f"  Active: {status['capability_space']['active']}")
    print(f"  Underperforming: {status['capability_space']['underperforming']}")
    print(f"  Active Gaps: {status['gaps']['active']}")
    print(f"  Total Innovations: {status['innovations']['total']}")
    print(f"  Integration Rate: {status['integration_rate']:.1%}")
    
    # Get detailed report
    report = engine.get_discovery_report()
    
    print("\nPending Innovations:")
    for innov in report['pending_innovations'][:3]:
        print(f"  - {innov['name']} (Stage: {innov['stage']})")
        print(f"    Expected improvement: {innov['estimated_improvement']:.2%}")


async def run_all_examples():
    """Run all examples"""
    await example_basic_usage()
    await example_with_trading_system()
    await example_manual_discovery()
    await example_gap_analysis()
    await example_integration_hooks()
    await example_constraint_configuration()
    await example_rollback()
    await example_reporting()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_examples())
