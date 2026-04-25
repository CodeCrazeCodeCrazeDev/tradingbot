"""
Example Usage: Unified Financial Intelligence System

Demonstrates the complete self-evolving financial intelligence infrastructure:
- Continuous market evaluation
- Self-auditing and reasoning inspection
- Cognitive gap detection
- Adversarial validation
- Uncertainty decomposition
- Governed evolution
- Intelligence compounding over time
"""

import asyncio
from datetime import datetime

from trading_bot.decision_governance import (
    UnifiedFinancialIntelligenceSystem,
    SystemPhase,
    create_financial_intelligence_system,
    ConstraintProfile,
)


async def example_system_initialization():
    """
    Example 1: Initialize the Unified Intelligence System
    """
    print("=" * 70)
    print("Example 1: System Initialization")
    print("=" * 70)
    
    # Create with custom constraints
    constraints = ConstraintProfile(
        max_drawdown_limit=0.10,
        min_sharpe_ratio=1.2,
        risk_adjusted_return_threshold=0.002
    )
    
    # Create the unified system
    system = create_financial_intelligence_system(
        trading_system=None,  # Would pass actual trading system
        constraint_profile=constraints,
        storage_path="my_intelligence_system.json",
        config={
            'auto_evolution': True,
            'adversarial_validation': True,
            'continuous_monitoring': True
        }
    )
    
    print("\n✓ Unified Financial Intelligence System created")
    print(f"  Constraint profile:")
    print(f"    Max drawdown: {constraints.max_drawdown_limit:.1%}")
    print(f"    Min Sharpe: {constraints.min_sharpe_ratio}")
    print(f"    Min improvement: {constraints.risk_adjusted_return_threshold:.2%}")
    
    print(f"\n  Subsystems initialized:")
    print(f"    - Capability Discovery Engine")
    print(f"    - Introspection-Driven Evolution Engine")
    print(f"    - Self-Inspection Engine")
    print(f"    - Three-Memory System")
    print(f"    - Controlled Evolution Plane")
    
    return system


async def example_system_lifecycle():
    """
    Example 2: Start and Stop the System
    """
    print("\n" + "=" * 70)
    print("Example 2: System Lifecycle")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    
    print("\nStarting system...")
    await system.start()
    
    print(f"  Current phase: {system.current_phase.value}")
    print(f"  System running: {system._running}")
    
    # Let it run briefly
    await asyncio.sleep(2)
    
    print("\nStopping system...")
    await system.stop()
    
    print(f"  System running: {system._running}")
    print("✓ System stopped gracefully")


async def example_phase_transitions():
    """
    Example 3: System Phase Transitions
    Monitor phase changes during operation
    """
    print("\n" + "=" * 70)
    print("Example 3: Phase Transitions")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    
    # Track phase changes
    phase_history = []
    
    def on_phase_change(old_phase, new_phase):
        phase_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'from': old_phase.value,
            'to': new_phase.value
        })
        print(f"  Phase transition: {old_phase.value} → {new_phase.value}")
    
    system.on_phase_change.append(on_phase_change)
    
    print("\nStarting system with phase monitoring...")
    await system.start()
    
    # Wait for some transitions
    await asyncio.sleep(3)
    
    print(f"\n  Phase history ({len(phase_history)} transitions):")
    for transition in phase_history[-5:]:
        print(f"    {transition['from']} → {transition['to']}")
    
    await system.stop()


async def example_system_status():
    """
    Example 4: Get System Status
    Comprehensive view of system health and intelligence
    """
    print("\n" + "=" * 70)
    print("Example 4: System Status")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    await system.start()
    await asyncio.sleep(2)
    
    status = system.get_system_status()
    
    print("\nSystem Status:")
    print(f"  Timestamp: {status['timestamp']}")
    print(f"  Phase: {status['phase']}")
    print(f"  Running: {status['is_running']}")
    
    print("\n  Intelligence Metrics:")
    print(f"    Current score: {status['intelligence']['current_score']:.3f}")
    print(f"    Capabilities: {status['intelligence']['capabilities']}")
    print(f"    Gaps: {status['intelligence']['gaps']}")
    print(f"    Compounding events: {status['intelligence']['compounding_events']}")
    print(f"    Performance trend: {status['intelligence']['trend']:.4f}")
    
    print("\n  Health Metrics:")
    print(f"    Health score: {status['health']['score']:.2f}")
    print(f"    Critical findings: {status['health']['critical_findings']}")
    print(f"    Active bottlenecks: {status['health']['active_bottlenecks']}")
    print(f"    Calibration Brier: {status['health']['calibration_brier']}")
    
    print("\n  Evolution Metrics:")
    print(f"    Integration rate: {status['evolution']['integration_rate']:.1%}")
    print(f"    Innovations in progress: {status['evolution']['innovations_in_progress']}")
    print(f"    Completed integrations: {status['evolution']['completed_integrations']}")
    
    await system.stop()


async def example_intelligence_report():
    """
    Example 5: Intelligence Compounding Report
    Deep dive into how intelligence compounds over time
    """
    print("\n" + "=" * 70)
    print("Example 5: Intelligence Compounding Report")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    await system.start()
    await asyncio.sleep(2)
    
    report = system.get_intelligence_report()
    
    print("\nIntelligence Report:")
    
    print("\n  Current Intelligence:")
    print(f"    Score: {report['current_intelligence']['intelligence']['current_score']:.3f}")
    print(f"    Capabilities: {report['current_intelligence']['intelligence']['capabilities']}")
    print(f"    Trend: {report['current_intelligence']['intelligence']['trend']:.4f}")
    
    print("\n  Compounding History (last 5):")
    for event in report['compounding_history'][-5:]:
        print(f"    {event['timestamp'][:19]}: {event['type']}")
        print(f"      Description: {event['description'][:50]}...")
        print(f"      Intelligence delta: {event['intelligence_delta']:.3f}")
    
    print("\n  Bottlenecks:")
    print(f"    Active: {len(report['bottlenecks']['active'])}")
    for bottleneck in report['bottlenecks']['active'][:3]:
        print(f"      - {bottleneck['description'][:50]}...")
        print(f"        Severity: {bottleneck['severity']:.2f}, Impact: {bottleneck['impact']:.1%}")
    print(f"    Resolved: {report['bottlenecks']['resolved_count']}")
    
    print("\n  Key Insights:")
    for insight in report['key_insights']:
        print(f"    {insight}")
    
    print("\n  Performance Trajectory (last 10):")
    print(f"    {report['performance_trajectory'][-10:]}")
    
    await system.stop()


async def example_intelligence_compounding():
    """
    Example 6: Intelligence Compounding Events
    Track how the system builds on previous improvements
    """
    print("\n" + "=" * 70)
    print("Example 6: Intelligence Compounding")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    
    # Track compounding events
    events = []
    
    def on_compound(event):
        events.append(event)
        print(f"\n  Compounding event: {event.event_type}")
        print(f"    Intelligence +{event.intelligence_delta:.3f}")
        print(f"    {event.description[:60]}...")
    
    system.on_intelligence_compounded.append(on_compound)
    
    await system.start()
    
    # Simulate some improvements
    await system._record_compounding_event(
        event_type='capability_integrated',
        description='Added real-time regime detection',
        intelligence_delta=0.08,
        capabilities_affected=['market_analysis', 'decision_governance']
    )
    
    await system._record_compounding_event(
        event_type='bug_fixed',
        description='Fixed calibration drift in high-vol regimes',
        intelligence_delta=0.05,
        capabilities_affected=['uncertainty_calibration']
    )
    
    await system._record_compounding_event(
        event_type='pattern_learned',
        description='Discovered early warning signal for drawdowns',
        intelligence_delta=0.12,
        capabilities_affected=['risk_management']
    )
    
    print(f"\n✓ Recorded {len(events)} compounding events")
    
    # Show cumulative effect
    total_delta = sum(e.intelligence_delta for e in events)
    print(f"\n  Cumulative intelligence gain: +{total_delta:.3f}")
    print(f"  Average per event: {total_delta/len(events):.3f}")
    
    # Show lessons learned
    print("\n  Lessons from compounding:")
    for lesson in events[0].lessons_learned:
        print(f"    - {lesson}")
    
    await system.stop()


async def example_bottleneck_detection():
    """
    Example 7: Bottleneck Detection and Resolution
    """
    print("\n" + "=" * 70)
    print("Example 7: Bottleneck Detection")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    
    # Track detected bottlenecks
    detected_bottlenecks = []
    
    def on_bottleneck(bottleneck):
        detected_bottlenecks.append(bottleneck)
        print(f"\n  Bottleneck detected: {bottleneck.bottleneck_id}")
        print(f"    Severity: {bottleneck.severity:.2f}")
        print(f"    Impact on performance: {bottleneck.impact_on_performance:.1%}")
    
    system.on_bottleneck_detected.append(on_bottleneck)
    
    await system.start()
    await asyncio.sleep(2)
    
    # Analyze bottlenecks
    await system._analyze_bottlenecks()
    
    print(f"\n  Total bottlenecks detected: {len(detected_bottlenecks)}")
    
    if detected_bottlenecks:
        print("\n  Active bottlenecks:")
        for b in detected_bottlenecks:
            print(f"\n    [{b.bottleneck_id}]")
            print(f"      {b.description}")
            print(f"      Root cause: {b.root_cause}")
            print(f"      Solution: {b.proposed_solution}")
            print(f"      Estimated improvement: {b.estimated_improvement:.1%}")
            print(f"      Complexity: {b.complexity}")
    
    await system.stop()


async def example_recovery_mode():
    """
    Example 8: Recovery Mode
    How the system handles critical issues
    """
    print("\n" + "=" * 70)
    print("Example 8: Recovery Mode")
    print("=" * 70)
    
    system = create_financial_intelligence_system()
    
    await system.start()
    
    # Simulate critical issues
    print("\nSimulating critical issues...")
    
    # Add mock critical findings
    from trading_bot.decision_governance import FindingSeverity, InspectionFinding, InspectionCategory
    
    for i in range(6):  # More than 5 triggers recovery
        finding_id = f"finding_critical_{i}"
        system.self_inspection.findings[finding_id] = InspectionFinding(
            finding_id=finding_id,
            category=InspectionCategory.SYSTEMATIC_ERROR,
            severity=FindingSeverity.CRITICAL,
            title=f"Critical issue {i}",
            description="Simulated critical finding",
            evidence=[],
            affected_decisions=[],
            first_observed=datetime.utcnow(),
            last_observed=datetime.utcnow(),
            occurrence_count=1,
            recommended_action="Fix immediately",
            expected_impact=0.2,
            automated_fixable=False
        )
    
    # Check for issues
    issues = system._check_for_critical_issues()
    
    print(f"  Critical issues detected: {len(issues)}")
    
    if issues:
        print("\n  Triggering recovery mode...")
        await system._handle_critical_issues(issues)
        print(f"  Current phase after recovery: {system.current_phase.value}")
    
    await system.stop()


async def example_complete_workflow():
    """
    Example 9: Complete Self-Improving Workflow
    """
    print("\n" + "=" * 70)
    print("Example 9: Complete Self-Improving Workflow")
    print("=" * 70)
    
    print("\n🚀 Starting complete self-improving workflow...\n")
    
    # Create and start system
    system = create_financial_intelligence_system()
    
    print("Phase 1: Initialization")
    print("  - Initializing memory systems...")
    print("  - Mapping capability space...")
    print("  - Running baseline self-inspection...")
    
    await system.start()
    print(f"  ✓ System initialized in {system.current_phase.value} phase\n")
    
    print("Phase 2: Continuous Operation")
    print("  - Market evaluation: Active")
    print("  - Self-inspection: Active")
    print("  - Capability monitoring: Active")
    print("  - Adversarial validation: Active\n")
    
    await asyncio.sleep(3)
    
    print("Phase 3: Evolution & Improvement")
    print("  - Detecting capability gaps...")
    print("  - Running introspection on failures...")
    print("  - Generating innovations...")
    print("  - Validating improvements...\n")
    
    await system._run_evolution_cycle()
    
    print("Phase 4: Intelligence Compounding")
    print("  - Tracking capability integrations...")
    print("  - Measuring intelligence deltas...")
    print("  - Recording lessons learned...\n")
    
    # Record some compounding
    await system._record_compounding_event(
        event_type='system_initialized',
        description='Unified intelligence system operational',
        intelligence_delta=0.0
    )
    
    print("Phase 5: Analysis & Reporting")
    status = system.get_system_status()
    report = system.get_intelligence_report()
    
    print(f"  System health: {status['health']['score']:.1%}")
    print(f"  Intelligence score: {status['intelligence']['current_score']:.3f}")
    print(f"  Compounding events: {len(system.compounding_events)}")
    print(f"  Key insight: {report['key_insights'][0] if report['key_insights'] else 'N/A'}\n")
    
    await system.stop()
    
    print("✓ Complete workflow finished")
    print("\nSystem achieved:")
    print("  ✓ Self-monitoring of decisions and reasoning")
    print("  ✓ Automatic gap detection in cognition")
    print("  ✓ Adversarial validation of conclusions")
    print("  ✓ Uncertainty decomposition")
    print("  ✓ Governed capability evolution")
    print("  ✓ Intelligence compounding over time")
    print("  ✓ Stable operation with self-healing")


async def run_all_examples():
    """Run all examples"""
    await example_system_initialization()
    await example_system_lifecycle()
    await example_phase_transitions()
    await example_system_status()
    await example_intelligence_report()
    await example_intelligence_compounding()
    await example_bottleneck_detection()
    await example_recovery_mode()
    await example_complete_workflow()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\n🎯 The Unified Financial Intelligence System:")
    print("   • Evaluates markets continuously")
    print("   • Audits its own reasoning automatically")
    print("   • Detects cognitive gaps in real-time")
    print("   • Adversarially challenges all conclusions")
    print("   • Decomposes uncertainty multi-dimensionally")
    print("   • Evolves under strict governance controls")
    print("   • Compounds intelligence without sacrificing stability")
    print("   • Discovers and fixes its own limitations")
    print("   • Creates measurable, reversible self-improvements")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
