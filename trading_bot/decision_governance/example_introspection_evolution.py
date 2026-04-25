"""
Example Usage: Introspection-Driven Evolution Engine

Demonstrates how to use the introspection system to:
1. Explain WHY failures happened with deep causal analysis
2. Prescribe specific fixes with implementation steps
3. Generate capability gaps automatically
4. Execute the complete evolution loop
"""

import asyncio
from datetime import datetime

from trading_bot.decision_governance import (
    IntrospectionDrivenEvolutionEngine,
    RootCauseCategory,
    FixComplexity,
    create_introspection_evolution_engine,
    # Memory systems for integration
    DecisionMemory,
    OutcomeMemory,
    FailureMemory,
    ContinuousCapabilityDiscoveryEngine,
)


async def example_basic_introspection():
    """
    Example 1: Basic Failure Introspection
    Introspect a single failure to understand WHY it happened
    """
    print("=" * 70)
    print("Example 1: Basic Failure Introspection")
    print("=" * 70)
    
    # Create the introspection engine
    engine = create_introspection_evolution_engine()
    
    # Simulate introspecting a failure
    decision_id = "trade_20240101_001"
    
    result = await engine.introspect_failure(decision_id)
    
    if result:
        print(f"\nIntrospection complete for: {decision_id}")
        print(f"Priority: {result.priority:.2f}")
        print(f"Estimated impact if fixed: {result.estimated_impact:.2%}")
        
        # Show explanation
        print("\n" + "-" * 70)
        print("EXPLANATION:")
        print("-" * 70)
        print(result.explanation.summary)
        print("\nDetailed narrative:")
        print(result.explanation.detailed_narrative[:500] + "...")
        
        # Show lessons
        print("\n" + "-" * 70)
        print("LESSONS LEARNED:")
        print("-" * 70)
        for lesson in result.explanation.lessons:
            print(f"  - {lesson}")
        
        # Show prescribed fixes
        print("\n" + "-" * 70)
        print("PRESCRIBED FIXES:")
        print("-" * 70)
        for fix in result.prescribed_fixes:
            print(f"\n  Fix ID: {fix.fix_id}")
            print(f"  Description: {fix.description}")
            print(f"  Complexity: {fix.complexity.value}")
            print(f"  Expected improvement: {fix.expected_improvement:.2%}")
            print(f"  Can be automated: {fix.automated}")


async def example_causal_analysis():
    """
    Example 2: Deep Causal Analysis
    Understanding the complete causal chain from root cause to failure
    """
    print("\n" + "=" * 70)
    print("Example 2: Deep Causal Analysis")
    print("=" * 70)
    
    engine = create_introspection_evolution_engine()
    
    # Introspect a failure
    decision_id = "trade_20240101_002"
    result = await engine.introspect_failure(decision_id)
    
    if result and result.explanation.causal_chain:
        print(f"\nCausal chain for failure: {decision_id}")
        print("\nChain from ROOT cause to immediate cause:")
        print("-" * 70)
        
        for i, factor in enumerate(result.explanation.causal_chain, 1):
            marker = " 🎯 ROOT CAUSE" if factor.is_root else ""
            print(f"\n{i}. {factor.description}{marker}")
            print(f"   Category: {factor.category.value}")
            print(f"   Confidence: {factor.confidence:.0%}")
            if factor.evidence:
                print(f"   Evidence: {factor.evidence[0]}")
        
        # Show counterfactual
        print("\n" + "-" * 70)
        print("COUNTERFACTUAL (What would have prevented this):")
        print("-" * 70)
        print(result.explanation.counterfactual)


async def example_fix_prescription():
    """
    Example 3: Fix Prescription by Category
    See how different root cause categories generate different fixes
    """
    print("\n" + "=" * 70)
    print("Example 3: Fix Prescription by Root Cause Category")
    print("=" * 70)
    
    engine = create_introspection_evolution_engine()
    
    categories = [
        RootCauseCategory.MODEL_DEFICIENCY,
        RootCauseCategory.CALIBRATION_DRIFT,
        RootCauseCategory.REGIME_MISMATCH,
        RootCauseCategory.RISK_MANAGEMENT,
    ]
    
    for category in categories:
        print(f"\n{'='*70}")
        print(f"Category: {category.value.upper()}")
        print('='*70)
        
        # Get fix templates for this category
        templates = engine._get_fix_templates(category)
        
        for i, template in enumerate(templates[:2], 1):  # Show top 2
            print(f"\n{i}. {template['description']}")
            print(f"   Type: {template['fix_type']}")
            print(f"   Complexity: {template['complexity'].value}")
            print(f"   Expected improvement: {template['expected_improvement']:.2%}")
            print(f"   Implementation steps:")
            for step in template['implementation_steps'][:2]:  # Show first 2 steps
                print(f"      - {step}")


async def example_evolution_loop():
    """
    Example 4: Complete Evolution Loop
    From failure detection → introspection → fix prescription → capability generation
    """
    print("\n" + "=" * 70)
    print("Example 4: Complete Evolution Loop")
    print("=" * 70)
    
    # Create capability discovery engine
    capability_engine = create_introspection_evolution_engine()
    
    # Start evolution loop for a failure
    failure_id = "trade_20240101_003"
    
    print(f"\nStarting evolution loop for: {failure_id}")
    print("\nEvolution Loop Flow:")
    print("  1. Introspect failure → explain WHY")
    print("  2. Prescribe fixes → specific solutions")
    print("  3. Create capability gaps → feed discovery")
    print("  4. Innovate → generate improvements")
    print("  5. Validate → test solutions")
    print("  6. Integrate → deploy improvements")
    
    # Start the loop
    loop_record = await capability_engine.start_evolution_loop(
        failure_id=failure_id,
        auto_execute_immediate=True
    )
    
    if loop_record:
        print(f"\n✓ Evolution loop started: {loop_record.loop_id}")
        print(f"  Status: {loop_record.outcome}")
        
        # Get introspection details
        introspection = capability_engine.introspections.get(loop_record.introspection_id)
        if introspection:
            print(f"\n  Root cause identified: {introspection.explanation.causal_chain[0].category.value if introspection.explanation.causal_chain else 'unknown'}")
            print(f"  Fixes prescribed: {len(introspection.prescribed_fixes)}")
            print(f"  Capability gaps created: {len(introspection.capability_gaps_created)}")


async def example_integration_with_capability_discovery():
    """
    Example 5: Integration with Capability Discovery
    Show how introspection automatically feeds capability discovery
    """
    print("\n" + "=" * 70)
    print("Example 5: Integration with Capability Discovery")
    print("=" * 70)
    
    # Create both engines
    capability_discovery = ContinuousCapabilityDiscoveryEngine()
    
    introspection_engine = create_introspection_evolution_engine(
        capability_discovery_engine=capability_discovery
    )
    
    # Introspect a failure
    failure_id = "trade_20240101_004"
    result = await introspection_engine.introspect_failure(
        failure_id,
        auto_generate_fixes=True,
        auto_create_gaps=True
    )
    
    if result:
        print(f"\n✓ Introspection complete for: {failure_id}")
        print(f"  Capability gaps created: {len(result.capability_gaps_created)}")
        
        # Show gaps in capability discovery
        print(f"\n  Active gaps in capability discovery:")
        for gap_id in result.capability_gaps_created[:3]:
            if gap_id in capability_discovery.active_gaps:
                gap = capability_discovery.active_gaps[gap_id]
                print(f"    - {gap_id}: {gap.description[:50]}...")
                print(f"      Severity: {gap.severity:.2f}, Impact: {gap.impact_score:.2%}")


async def example_fix_effectiveness_tracking():
    """
    Example 6: Fix Effectiveness Tracking
    Track whether prescribed fixes actually work
    """
    print("\n" + "=" * 70)
    print("Example 6: Fix Effectiveness Tracking")
    print("=" * 70)
    
    engine = create_introspection_evolution_engine()
    
    # Simulate completing an evolution loop
    loop_id = "loop_test_001"
    
    # First create a loop
    introspection_id = "introspect_test_001"
    engine.introspections[introspection_id] = type('obj', (object,), {
        'prescribed_fixes': [type('fix', (object,), {'fix_id': 'fix_001', 'expected_improvement': 0.12})]
    })()
    
    engine.active_loops[loop_id] = type('obj', (object,), (object,), {
        'loop_id': loop_id,
        'introspection_id': introspection_id,
        'outcome': 'in_progress'
    })()
    
    # Complete the loop with success
    engine.complete_evolution_loop(
        loop_id=loop_id,
        innovation_id="innov_001",
        experiment_id="exp_001",
        outcome="success",
        actual_improvement=0.10,
        lessons=["Fix was effective", "Monitoring validated improvement"]
    )
    
    print(f"\n✓ Evolution loop completed: {loop_id}")
    print(f"  Predicted improvement: 12%")
    print(f"  Actual improvement: 10%")
    print(f"  Effectiveness ratio: {0.10/0.12:.1%}")
    
    # Get summary
    summary = engine.get_evolution_summary()
    print(f"\nEvolution Summary:")
    print(f"  Total introspections: {summary['introspections']['total']}")
    print(f"  Evolution loops: {summary['evolution_loops']['active']} active")
    print(f"  Completed successfully: {summary['evolution_loops']['completed_success']}")
    print(f"  Success rate: {summary['evolution_loops']['success_rate']:.1%}")


async def example_reporting():
    """
    Example 7: Introspection Reporting
    Generate comprehensive reports on failures and fixes
    """
    print("\n" + "=" * 70)
    print("Example 7: Introspection Reporting")
    print("=" * 70)
    
    engine = create_introspection_evolution_engine()
    
    # Generate a few introspections first
    for i in range(3):
        await engine.introspect_failure(f"trade_20240101_{i+100}")
    
    # Get summary report
    summary = engine.get_evolution_summary()
    
    print("\n" + "-" * 70)
    print("INTROSPECTION STATISTICS")
    print("-" * 70)
    print(f"Total introspections: {summary['introspections']['total']}")
    print(f"Pending: {summary['introspections']['pending']}")
    print(f"By category:")
    for category, count in summary['introspections']['by_category'].items():
        print(f"  - {category}: {count}")
    
    print("\n" + "-" * 70)
    print("FIX STATISTICS")
    print("-" * 70)
    print(f"Total prescribed: {summary['fixes']['total_prescribed']}")
    print(f"Automated (immediate): {summary['fixes']['automated']}")
    print(f"Manual (requires work): {summary['fixes']['manual']}")
    
    # Get detailed report for one introspection
    introspection_ids = list(engine.introspections.keys())
    if introspection_ids:
        report = engine.get_introspection_report(introspection_ids[0])
        if report:
            print("\n" + "-" * 70)
            print("SAMPLE INTROSPECTION REPORT")
            print("-" * 70)
            print(f"Introspection ID: {report['introspection_id']}")
            print(f"Failure ID: {report['failure_id']}")
            print(f"Timestamp: {report['timestamp']}")
            print(f"Status: {report['status']}")
            print(f"Priority: {report['priority']:.2f}")
            print(f"\nSummary: {report['explanation']['summary']}")
            print(f"\nCounterfactual: {report['explanation']['counterfactual']}")


async def example_automated_fixes():
    """
    Example 8: Automated Immediate Fixes
    Execute fixes that can be applied automatically
    """
    print("\n" + "=" * 70)
    print("Example 8: Automated Immediate Fixes")
    print("=" * 70)
    
    engine = create_introspection_evolution_engine()
    
    # Add callback for when fixes are applied
    def on_fix_applied(fix, failure_id, success):
        print(f"\n✓ Fix applied automatically:")
        print(f"  Fix ID: {fix.fix_id}")
        print(f"  Failure: {failure_id}")
        print(f"  Description: {fix.description[:60]}...")
        print(f"  Success: {success}")
    
    engine.on_fix_prescribed.append(on_fix_applied)
    
    # Start evolution loop with auto-execute
    failure_id = "trade_20240101_005"
    
    print(f"\nStarting evolution loop with auto-execution...")
    print(f"  Failure: {failure_id}")
    
    loop_record = await engine.start_evolution_loop(
        failure_id=failure_id,
        auto_execute_immediate=True
    )
    
    if loop_record:
        # Check which fixes were automated
        introspection = engine.introspections.get(loop_record.introspection_id)
        if introspection:
            automated_fixes = [f for f in introspection.prescribed_fixes if f.automated]
            print(f"\n✓ {len(automated_fixes)} automated fixes applied immediately")
            
            manual_fixes = [f for f in introspection.prescribed_fixes if not f.automated]
            if manual_fixes:
                print(f"  {len(manual_fixes)} manual fixes require implementation")
                for fix in manual_fixes:
                    print(f"    - [{fix.complexity.value}] {fix.description[:50]}...")


async def run_all_examples():
    """Run all examples"""
    await example_basic_introspection()
    await example_causal_analysis()
    await example_fix_prescription()
    await example_evolution_loop()
    await example_integration_with_capability_discovery()
    await example_fix_effectiveness_tracking()
    await example_reporting()
    await example_automated_fixes()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Every failure gets deep causal analysis (WHY)")
    print("  2. Fixes are prescribed with implementation steps")
    print("  3. Complex fixes become capability gaps for discovery")
    print("  4. Immediate fixes can be applied automatically")
    print("  5. Effectiveness is tracked to learn what works")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
