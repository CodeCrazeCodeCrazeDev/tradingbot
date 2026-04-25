"""
Example Usage: Self-Inspection and Meta-Learning Engine

Demonstrates how to use the SelfInspectionEngine to:
1. Inspect decisions, reasoning artifacts, uncertainty, and outcomes
2. Detect errors, limitations, and improvement opportunities
3. Perform real-time continuous self-monitoring
4. Integrate with capability discovery for automatic improvements
"""

import asyncio
from datetime import datetime

from trading_bot.decision_governance import (
    SelfInspectionEngine,
    InspectionCategory,
    FindingSeverity,
    create_self_inspection_engine,
    create_continuous_discovery_engine,
    DecisionMemory,
    OutcomeMemory,
    FailureMemory,
)


async def example_basic_inspection():
    """
    Example 1: Basic Self-Inspection
    Run a one-time inspection of recent decisions
    """
    print("=" * 70)
    print("Example 1: Basic Self-Inspection")
    print("=" * 70)
    
    # Create the inspection engine
    engine = create_self_inspection_engine()
    
    # Run a full inspection
    results = await engine._run_full_inspection()
    
    print("\nInspection Results:")
    print(f"  Timestamp: {results['timestamp']}")
    print(f"\n  Decision Inspection: {results['decisions'].get('status', 'unknown')}")
    print(f"    Decisions inspected: {results['decisions'].get('decisions_inspected', 0)}")
    print(f"    Findings generated: {results['decisions'].get('findings_generated', 0)}")
    
    print(f"\n  Calibration Analysis: {results['calibration'].get('status', 'unknown')}")
    if 'brier_score' in results['calibration']:
        print(f"    Brier score: {results['calibration']['brier_score']:.4f}")
        print(f"    Max calibration gap: {results['calibration']['max_calibration_gap']:.2f}")
    
    print(f"\n  Error Patterns: {results['errors'].get('status', 'unknown')}")
    print(f"    Patterns detected: {results['errors'].get('patterns_detected', 0)}")
    
    print(f"\n  Biases Detected: {len(results['biases'].get('biases_detected', []))}")
    print(f"    Types: {results['biases'].get('bias_types', [])}")
    
    print(f"\n  Improvement Opportunities: {len(results['opportunities'])}")


async def example_continuous_monitoring():
    """
    Example 2: Continuous Self-Monitoring
    Start real-time inspection that runs automatically
    """
    print("\n" + "=" * 70)
    print("Example 2: Continuous Self-Monitoring")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Start continuous inspection (runs every 30 minutes by default)
    await engine.start_continuous_inspection(interval_minutes=30)
    
    print("\n✓ Continuous inspection started")
    print("  Status: Monitoring decisions, calibration, and errors")
    print("  Interval: Every 30 minutes")
    
    # Let it run for a few seconds
    await asyncio.sleep(2)
    
    # Get current summary
    summary = engine.get_inspection_summary()
    
    print(f"\n  Active findings: {summary['findings']['total']}")
    print(f"  Critical findings: {summary['findings']['critical']}")
    print(f"  High priority findings: {summary['findings']['high']}")
    
    # Stop monitoring
    await engine.stop_continuous_inspection()
    print("\n✓ Continuous inspection stopped")


async def example_inspection_findings():
    """
    Example 3: Working with Inspection Findings
    Retrieve and analyze findings by severity and category
    """
    print("\n" + "=" * 70)
    print("Example 3: Inspection Findings Analysis")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Run inspection to generate findings
    await engine._run_full_inspection()
    
    # Get inspection summary
    summary = engine.get_inspection_summary()
    
    print("\nFindings Summary:")
    print(f"  Total findings: {summary['findings']['total']}")
    print(f"  By severity: {summary['findings']['by_severity']}")
    print(f"  By category: {summary['findings']['by_category']}")
    
    # Get critical findings
    print("\n" + "-" * 70)
    print("CRITICAL FINDINGS:")
    print("-" * 70)
    
    critical = engine.get_findings_report(severity=FindingSeverity.CRITICAL)
    for finding in critical[:3]:
        print(f"\n  [{finding['severity'].upper()}] {finding['title']}")
        print(f"  Description: {finding['description'][:80]}...")
        print(f"  Occurrences: {finding['occurrence_count']}")
        print(f"  Recommendation: {finding['recommended_action']}")
        print(f"  Expected impact: {finding['expected_impact']:.1%}")
    
    # Get calibration-related findings
    print("\n" + "-" * 70)
    print("CALIBRATION FINDINGS:")
    print("-" * 70)
    
    calibration = engine.get_findings_report(
        category=InspectionCategory.UNCERTAINTY_CALIBRATION
    )
    for finding in calibration[:3]:
        print(f"\n  [{finding['severity'].upper()}] {finding['title']}")
        print(f"  {finding['description']}")
        print(f"  Automated fixable: {finding['automated_fixable']}")


async def example_decision_quality_analysis():
    """
    Example 4: Decision Quality Metrics
    Analyze quality of specific decisions
    """
    print("\n" + "=" * 70)
    print("Example 4: Decision Quality Analysis")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Mock decision quality metrics
    print("\n  Analyzing decision quality metrics...")
    
    # Calculate metrics for recent decisions
    await engine._inspect_recent_decisions(lookback_days=7)
    
    print(f"\n  Decision metrics computed: {len(engine.decision_metrics)}")
    
    # Show sample metrics
    for decision_id, metrics in list(engine.decision_metrics.items())[:3]:
        print(f"\n  Decision: {decision_id}")
        print(f"    Predicted confidence: {metrics.predicted_confidence:.2f}")
        print(f"    Actual outcome: {metrics.actual_outcome:.2%}" if metrics.actual_outcome else "    Actual outcome: N/A")
        print(f"    Calibration error: {metrics.calibration_error:.2f}" if metrics.calibration_error else "    Calibration error: N/A")
        print(f"    Evidence coverage: {metrics.evidence_coverage:.1%}")
        print(f"    Regime fit: {metrics.regime_fit:.2f}")
        print(f"    Robustness score: {metrics.robustness_score:.2f}")


async def example_calibration_tracking():
    """
    Example 5: Uncertainty Calibration Tracking
    Monitor how well system confidence predicts actual outcomes
    """
    print("\n" + "=" * 70)
    print("Example 5: Calibration Tracking")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Analyze calibration
    calibration_result = engine._analyze_calibration()
    
    print(f"\nCalibration Analysis: {calibration_result['status']}")
    
    if calibration_result['status'] == 'completed':
        print(f"\n  Brier Score: {calibration_result['brier_score']:.4f}")
        print(f"    (Lower is better, 0.25 = random)")
        
        print(f"\n  Max Calibration Gap: {calibration_result['max_calibration_gap']:.2f}")
        print(f"    (Ideal: < 0.1, Poor: > 0.2)")
        
        if calibration_result['systematic_underconfidence']:
            print("\n  ⚠️ Systematic underconfidence detected")
            print("     Model is too conservative")
        
        if calibration_result['systematic_overconfidence']:
            print("\n  ⚠️ Systematic overconfidence detected")
            print("     Model is too optimistic")
        
        print(f"\n  Calibration improving: {calibration_result['is_improving']}")
        print(f"  Pairs analyzed: {calibration_result['pairs_analyzed']}")
        
        # Get calibration history
        if engine.calibration_history:
            print("\n  Recent calibration trend:")
            recent = list(engine.calibration_history)[-5:]
            for entry in recent:
                print(f"    {entry['timestamp']}: Brier={entry['brier']:.4f}, MaxGap={entry['max_gap']:.2f}")


async def example_bias_detection():
    """
    Example 6: Cognitive Bias Detection
    Detect systematic cognitive biases in decision making
    """
    print("\n" + "=" * 70)
    print("Example 6: Bias Detection")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Run bias detection
    bias_result = engine._detect_biases()
    
    print(f"\nBias Detection: {bias_result['status']}")
    print(f"  Biases detected: {bias_result['biases_detected']}")
    
    if bias_result['bias_types']:
        print("\n  Detected bias types:")
        for bias_type in bias_result['bias_types']:
            print(f"    - {bias_type.replace('_', ' ').title()}")
            
            # Get description
            descriptions = {
                'overconfidence': 'Decisions show excessive confidence relative to actual outcomes',
                'recency': 'Decisions overweight recent events vs. historical patterns',
                'confirmation': 'Evidence search disproportionately supports initial thesis',
                'loss_aversion': 'Risk-taking behavior changes after losses in ways that hurt performance'
            }
            print(f"      {descriptions.get(bias_type, 'Cognitive bias detected')}")
    
    # Show related findings
    print("\n  Related findings:")
    bias_findings = engine.get_findings_report(category=InspectionCategory.COGNITIVE_BIAS)
    for finding in bias_findings[:3]:
        print(f"\n    [{finding['severity'].upper()}] {finding['title']}")
        print(f"    Recommendation: {finding['recommended_action']}")


async def example_improvement_opportunities():
    """
    Example 7: Improvement Opportunity Mining
    Discover opportunities from successes and failures
    """
    print("\n" + "=" * 70)
    print("Example 7: Improvement Opportunities")
    print("=" * 70)
    
    engine = create_self_inspection_engine()
    
    # Mine opportunities
    opportunities = engine._identify_improvement_opportunities()
    
    print(f"\n✓ Identified {len(opportunities)} improvement opportunities")
    
    # Get detailed report
    report = engine.get_opportunities_report(min_priority=0.5)
    
    print(f"\n  High-priority opportunities: {len(report)}")
    
    print("\n" + "-" * 70)
    print("TOP OPPORTUNITIES:")
    print("-" * 70)
    
    for opp in report[:5]:
        print(f"\n  [{opp['priority']:.2f}] {opp['description'][:60]}...")
        print(f"  Source: {opp['source']}")
        print(f"  Complexity: {opp['complexity']}")
        print(f"  Expected improvement: {opp['estimated_improvement']:.1%}")
        print(f"  Approach: {opp['recommended_approach'][:60]}...")


async def example_integration_with_capability_discovery():
    """
    Example 8: Integration with Capability Discovery
    How inspection findings automatically create capability gaps
    """
    print("\n" + "=" * 70)
    print("Example 8: Integration with Capability Discovery")
    print("=" * 70)
    
    # Create capability discovery engine
    capability_discovery = create_continuous_discovery_engine()
    
    # Create self-inspection engine with integration
    inspection_engine = create_self_inspection_engine(
        capability_discovery_engine=capability_discovery
    )
    
    print("\n✓ Engines created with bidirectional integration")
    
    # Run inspection (which will feed opportunities to discovery)
    await inspection_engine._run_full_inspection()
    
    # Show capability gaps created
    print(f"\n  Capability gaps in discovery engine:")
    print(f"    Total active: {len(capability_discovery.active_gaps)}")
    
    # Show gaps by severity
    high_severity = [g for g in capability_discovery.active_gaps.values() if g.severity > 0.7]
    print(f"    High severity: {len(high_severity)}")
    
    for gap in list(capability_discovery.active_gaps.values())[:3]:
        print(f"\n    Gap: {gap.id[:40]}...")
        print(f"      Description: {gap.description[:50]}...")
        print(f"      Severity: {gap.severity:.2f}")
        print(f"      Impact score: {gap.impact_score:.1%}")


async def example_complete_workflow():
    """
    Example 9: Complete Self-Improving Workflow
    Demonstrate full cycle: inspect → find → create gaps → improve
    """
    print("\n" + "=" * 70)
    print("Example 9: Complete Self-Improving Workflow")
    print("=" * 70)
    
    # Setup
    capability_discovery = create_continuous_discovery_engine()
    
    engine = create_self_inspection_engine(
        capability_discovery_engine=capability_discovery
    )
    
    print("\n🔄 Starting self-improving workflow...")
    print("\n  Step 1: Run comprehensive self-inspection")
    
    # Step 1: Inspect
    results = await engine._run_full_inspection()
    
    findings_count = len(engine.findings)
    opportunities_count = len(engine.opportunities)
    
    print(f"    ✓ Generated {findings_count} findings")
    print(f"    ✓ Identified {opportunities_count} improvement opportunities")
    
    # Step 2: Review critical findings
    print("\n  Step 2: Review critical issues")
    critical = engine.get_findings_report(severity=FindingSeverity.CRITICAL)
    high = engine.get_findings_report(severity=FindingSeverity.HIGH)
    
    print(f"    Critical issues: {len(critical)}")
    print(f"    High priority issues: {len(high)}")
    
    # Step 3: Create capability gaps
    print("\n  Step 3: Feed to capability discovery")
    gaps_created = len(capability_discovery.active_gaps)
    print(f"    ✓ Created {gaps_created} capability gaps")
    
    # Step 4: Get summary
    print("\n  Step 4: System state summary")
    summary = engine.get_inspection_summary()
    
    print(f"    Monitoring: {'Active' if summary['monitoring']['active'] else 'Inactive'}")
    print(f"    Total findings: {summary['findings']['total']}")
    print(f"    Calibration: {summary['calibration']['current_brier']:.4f} Brier" if summary['calibration']['current_brier'] else "    Calibration: No data")
    print(f"    Opportunities: {summary['opportunities']['total']} (High priority: {summary['opportunities']['high_priority']})")
    
    print("\n✓ Self-improving workflow complete")
    print("  The system will now:")
    print("    - Continue monitoring for new issues")
    print("    - Validate capability improvements")
    print("    - Track fix effectiveness")
    print("    - Learn from outcomes")


async def run_all_examples():
    """Run all examples"""
    await example_basic_inspection()
    await example_continuous_monitoring()
    await example_inspection_findings()
    await example_decision_quality_analysis()
    await example_calibration_tracking()
    await example_bias_detection()
    await example_improvement_opportunities()
    await example_integration_with_capability_discovery()
    await example_complete_workflow()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Self-inspection runs automatically and continuously")
    print("  2. Every decision is analyzed for quality metrics")
    print("  3. Calibration is tracked over time with trend detection")
    print("  4. Cognitive biases are detected automatically")
    print("  5. Improvement opportunities mined from successes AND failures")
    print("  6. Findings automatically create capability gaps")
    print("  7. The system forms a complete self-improving loop")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
