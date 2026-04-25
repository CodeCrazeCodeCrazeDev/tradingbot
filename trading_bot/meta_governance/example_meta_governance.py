"""
Example Usage: Meta-Agent Optimization and Governance Layer

Demonstrates how the governance layer:
1. Monitors ALL agents in the trading bot
2. Detects underperforming behavior
3. Blocks forbidden changes (live execution, risk controls, capital limits)
4. Validates upgrades offline with strict criteria
5. Promotes only improvements that increase robustness, safety, economic value
"""

import asyncio
from datetime import datetime

from trading_bot.meta_governance import (
    MetaAgentGovernanceLayer,
    AgentType,
    ChangeType,
    ChangeCategory,
    create_meta_agent_governance_layer,
    ValidationCriteria,
)


async def example_initialization():
    """
    Example 1: Initialize the Meta-Agent Governance Layer
    """
    print("=" * 70)
    print("Example 1: Meta-Agent Governance Layer Initialization")
    print("=" * 70)
    
    # Create with strict validation criteria
    criteria = ValidationCriteria(
        minimum_trades=1000,  # NO tiny sample wins
        minimum_observations=5000,
        minimum_time_period_days=30,
        minimum_confidence_level=0.99,  # p < 0.01
        minimum_effect_size=0.15,  # 15% minimum improvement
        minimum_regime_robustness=0.7,  # Must work in 70% of regimes
        maximum_drawdown_increase=0.02,  # Max 2% DD increase
        risk_score_max=0.3,
        safety_incidents_max=0,
        minimum_sharpe_improvement=0.1,
        minimum_profit_factor=1.2,
        must_be_profitable=True,
    )
    
    governance = create_meta_agent_governance_layer(
        config={
            'strict_mode': True,
            'auto_promotion': False,  # Manual approval for extra safety
            'forbidden_patterns_strict': True,
        }
    )
    
    governance.validation_criteria = criteria
    
    print("\n✓ Meta-Agent Governance Layer created")
    print(f"  Minimum trades required: {criteria.minimum_trades}")
    print(f"  Minimum observations: {criteria.minimum_observations}")
    print(f"  Minimum improvement: {criteria.minimum_effect_size:.1%}")
    print(f"  Statistical confidence: {criteria.minimum_confidence_level:.1%}")
    print(f"  Regime robustness: {criteria.minimum_regime_robustness:.1%}")
    print(f"  Max DD increase: {criteria.maximum_drawdown_increase:.1%}")
    
    print("\n  STRICT PROHIBITIONS ENFORCED:")
    print("    ✗ NO rewriting live execution logic directly")
    print("    ✗ NO changing risk controls")
    print("    ✗ NO altering capital limits")
    print("    ✗ NO modifying governance thresholds without approval")
    print("    ✗ NO learning from contaminated labels")
    print("    ✗ NO promoting changes based on tiny sample wins")
    
    return governance


async def example_agent_monitoring():
    """
    Example 2: Monitor All Agents in the Trading Bot
    """
    print("\n" + "=" * 70)
    print("Example 2: Agent Monitoring")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print("\n  Monitoring all agent types:")
    for agent_type in AgentType:
        print(f"    - {agent_type.value}")
    
    # Run monitoring
    print("\n  Running agent monitoring cycle...")
    await governance._monitor_all_agents()
    
    print(f"\n✓ Monitoring complete")
    print(f"  Total agents monitored: {len(governance.agent_performance)}")
    
    # Show sample agent data
    if governance.agent_performance:
        print("\n  Sample agent performance:")
        for agent_id, perf in list(governance.agent_performance.items())[:3]:
            print(f"\n    {agent_id} ({perf.agent_type.value})")
            print(f"      Latency: {perf.latency_ms:.1f}ms (P95: {perf.latency_p95:.1f}ms)")
            print(f"      Error rate: {perf.error_rate:.2%}")
            print(f"      Economic contribution: ${perf.economic_contribution:,.2f}")
            print(f"      Net value: ${perf.net_value:,.2f}")
            print(f"      Contamination: {perf.contamination_ratio:.2%}")
            print(f"      Underperforming: {'YES' if perf.is_underperforming else 'NO'}")


async def example_underperformance_detection():
    """
    Example 3: Detect Underperforming Agents
    """
    print("\n" + "=" * 70)
    print("Example 3: Underperformance Detection")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    # Track detections
    detections = []
    
    def on_underperformance(performance):
        detections.append(performance)
        print(f"\n  ⚠️ Underperforming agent detected!")
        print(f"    Agent: {performance.agent_id}")
        print(f"    Type: {performance.agent_type.value}")
        print(f"    Reasons: {', '.join(performance.underperformance_reasons)}")
        print(f"    Severity: {performance.severity_score:.2f}")
        print(f"    Economic impact: ${performance.net_value:,.2f}")
    
    governance.on_underperformance_detected.append(on_underperformance)
    
    print("\n  Running detection cycle...")
    await governance._monitor_all_agents()
    await governance._detect_underperformance()
    
    print(f"\n✓ Detection complete")
    print(f"  Underperforming agents: {len(governance.underperforming_agents)}")
    print(f"  Total detections: {len(detections)}")


async def example_forbidden_change_blocking():
    """
    Example 4: Forbidden Change Detection and Blocking
    Shows how the system prevents dangerous changes
    """
    print("\n" + "=" * 70)
    print("Example 4: Forbidden Change Blocking")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    # Track blocked attempts
    blocked = []
    
    def on_blocked(attempt):
        blocked.append(attempt)
        print(f"\n  🚫 FORBIDDEN CHANGE BLOCKED!")
        print(f"    Attempt ID: {attempt.attempt_id}")
        print(f"    Agent: {attempt.agent_id}")
        print(f"    Type: {attempt.change_type.value}")
        print(f"    Severity: {attempt.severity}")
        print(f"    Action: {attempt.action_taken}")
    
    governance.on_forbidden_change_blocked.append(on_blocked)
    
    print("\n  Testing forbidden pattern detection:")
    
    # Test cases
    test_cases = [
        ("execute_trade(price, size)", "Direct execution call"),
        ("risk_limit = 0.05", "Risk limit modification"),
        ("capital_limit = 100000", "Capital limit change"),
        ("position_size = calculate_size()", "Position sizing change"),
        ("stop_loss = entry_price * 0.95", "Stop loss modification"),
        ("config_param = new_value", "Safe config change"),
    ]
    
    for code, description in test_cases:
        category, types, evidence = governance._scan_change_for_forbidden_patterns(
            code, description
        )
        
        status = "✗ BLOCKED" if category == ChangeCategory.FORBIDDEN else "✓ ALLOWED"
        print(f"\n    {status}: {description}")
        print(f"      Code: {code[:50]}")
        if category == ChangeCategory.FORBIDDEN:
            print(f"      Detected: {types[0].value if types else 'unknown'}")
    
    print(f"\n✓ Pattern detection active")
    print(f"  Blocked attempts: {len(blocked)}")


async def example_contaminated_label_detection():
    """
    Example 5: Contaminated Label Detection
    Prevents learning from bad data
    """
    print("\n" + "=" * 70)
    print("Example 5: Contaminated Label Detection")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print("\n  Checking agents for contaminated labels...")
    
    # Create mock performance with varying contamination levels
    test_cases = [
        ("agent_clean", 10, 5000, 0.2),  # Low contamination
        ("agent_borderline", 100, 5000, 2.0),  # Borderline
        ("agent_dirty", 500, 5000, 10.0),  # High contamination
    ]
    
    for agent_id, contaminated, clean, ratio in test_cases:
        # Create mock performance
        from trading_bot.meta_governance import AgentPerformance
        
        perf = AgentPerformance(
            agent_id=agent_id,
            agent_type=AgentType.SIGNAL_AGENT,
            agent_name="Test Agent",
            last_updated=datetime.utcnow(),
            measurement_window_days=30,
            latency_ms=50, latency_p95=100,
            error_rate=0.01, uptime_percent=99.9,
            output_quality_score=0.8,
            prediction_accuracy=0.65,
            signal_sharpe=1.2,
            economic_contribution=1000,
            cost_of_operation=200,
            net_value=800,
            performance_by_regime={},
            worst_regime_performance=-0.001,
            regime_robustness_score=0.75,
            decisions_count=1000,
            trades_count=500,
            observations_count=5000,
            contaminated_labels_used=contaminated,
            clean_labels_used=clean,
            contamination_ratio=ratio / 100,
            is_underperforming=False,
            underperformance_reasons=[],
            severity_score=0.0
        )
        
        is_contaminated = governance._detect_contaminated_labels(perf)
        
        status = "🚫 CONTAMINATED" if is_contaminated else "✓ CLEAN"
        print(f"\n    {status}: {agent_id}")
        print(f"      Contaminated labels: {contaminated}")
        print(f"      Clean labels: {clean}")
        print(f"      Contamination ratio: {ratio:.2f}%")
        print(f"      Threshold: 2.0%")
    
    print("\n✓ Contamination detection active")
    print("  Agents with >2% contaminated labels are flagged for remediation")


async def example_sample_size_validation():
    """
    Example 6: Sample Size Validation
    NO tiny sample wins allowed
    """
    print("\n" + "=" * 70)
    print("Example 6: Sample Size Validation (NO Tiny Sample Wins)")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print(f"\n  Minimum requirements:")
    print(f"    Trades: {governance.validation_criteria.minimum_trades}")
    print(f"    Observations: {governance.validation_criteria.minimum_observations}")
    print(f"    Time period: {governance.validation_criteria.minimum_time_period_days} days")
    
    print("\n  Testing sample size validation:")
    
    test_cases = [
        ("tiny_sample", 50, 100, "50 trades, 100 obs - TOO SMALL"),
        ("small_sample", 500, 2000, "500 trades, 2000 obs - TOO SMALL"),
        ("adequate_sample", 1500, 6000, "1500 trades, 6000 obs - ADEQUATE"),
        ("large_sample", 5000, 20000, "5000 trades, 20000 obs - EXCELLENT"),
    ]
    
    for agent_id, trades, obs, description in test_cases:
        from trading_bot.meta_governance import AgentPerformance
        
        perf = AgentPerformance(
            agent_id=agent_id,
            agent_type=AgentType.SIGNAL_AGENT,
            agent_name="Test Agent",
            last_updated=datetime.utcnow(),
            measurement_window_days=30,
            latency_ms=50, latency_p95=100,
            error_rate=0.01, uptime_percent=99.9,
            output_quality_score=0.8,
            prediction_accuracy=0.65,
            signal_sharpe=1.2,
            economic_contribution=1000,
            cost_of_operation=200,
            net_value=800,
            performance_by_regime={},
            worst_regime_performance=-0.001,
            regime_robustness_score=0.75,
            decisions_count=1000,
            trades_count=trades,
            observations_count=obs,
            contaminated_labels_used=10,
            clean_labels_used=5000,
            contamination_ratio=0.002,
            is_underperforming=False,
            underperformance_reasons=[],
            severity_score=0.0
        )
        
        is_adequate = governance._validate_sample_size(perf)
        
        status = "✓ PASS" if is_adequate else "✗ FAIL"
        print(f"\n    {status}: {description}")
    
    print("\n✓ Sample size validation active")
    print("  Promotions blocked until minimum sample size reached")


async def example_three_criteria_promotion():
    """
    Example 7: Three-Criteria Promotion Gate
    Must pass ALL: Robustness, Safety, Economic Value
    """
    print("\n" + "=" * 70)
    print("Example 7: Three-Criteria Promotion Gate")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print("\n  PROMOTION REQUIRES ALL THREE CRITERIA:")
    print("    1. ROBUSTNESS: Performance across market regimes")
    print("    2. SAFETY: Risk metrics and stress test results")
    print("    3. ECONOMIC VALUE: Profitable with good risk-adjusted returns")
    
    print("\n  Simulating validation results:")
    
    test_cases = [
        {
            'name': 'Perfect Candidate',
            'robustness': 0.85,
            'safety': 0.20,
            'economic': True,
            'sharpe': 0.20,
            'expected': 'PROMOTED'
        },
        {
            'name': 'Not Robust Enough',
            'robustness': 0.60,  # Below 0.70 threshold
            'safety': 0.20,
            'economic': True,
            'sharpe': 0.20,
            'expected': 'REJECTED'
        },
        {
            'name': 'Too Risky',
            'robustness': 0.85,
            'safety': 0.35,  # Above 0.30 threshold
            'economic': True,
            'sharpe': 0.20,
            'expected': 'REJECTED'
        },
        {
            'name': 'Not Profitable',
            'robustness': 0.85,
            'safety': 0.20,
            'economic': False,
            'sharpe': 0.20,
            'expected': 'REJECTED'
        },
    ]
    
    for case in test_cases:
        print(f"\n    Testing: {case['name']}")
        print(f"      Robustness: {case['robustness']:.2f} (need ≥0.70)")
        print(f"      Safety: {case['safety']:.2f} (need ≤0.30)")
        print(f"      Economic: {'YES' if case['economic'] else 'NO'}")
        
        # Check criteria
        robust_pass = case['robustness'] >= 0.70
        safety_pass = case['safety'] <= 0.30
        economic_pass = case['economic']
        
        all_pass = robust_pass and safety_pass and economic_pass
        result = 'PROMOTED' if all_pass else 'REJECTED'
        
        status_icon = "✓" if result == case['expected'] else "✗"
        print(f"      {status_icon} Result: {result}")
        
        if not all_pass:
            fails = []
            if not robust_pass:
                fails.append("Robustness")
            if not safety_pass:
                fails.append("Safety")
            if not economic_pass:
                fails.append("Economic Value")
            print(f"      Failed criteria: {', '.join(fails)}")
    
    print("\n✓ Three-criteria gate active")
    print("  ALL criteria must pass for promotion")


async def example_safe_upgrade_generation():
    """
    Example 8: Safe Upgrade Generation
    Only generates changes that don't violate prohibitions
    """
    print("\n" + "=" * 70)
    print("Example 8: Safe Upgrade Generation")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print("\n  Generating upgrades for underperforming agents...")
    
    # First detect underperforming agents
    await governance._monitor_all_agents()
    await governance._detect_underperformance()
    
    # Generate upgrades
    await governance._generate_safe_upgrades()
    
    print(f"\n✓ Generated {len(governance.candidate_upgrades)} candidate upgrades")
    
    if governance.candidate_upgrades:
        print("\n  Upgrade summary:")
        for upgrade in list(governance.candidate_upgrades.values())[:5]:
            print(f"\n    {upgrade.upgrade_id}")
            print(f"      Target: {upgrade.target_agent_id}")
            print(f"      Type: {upgrade.change_type.value}")
            print(f"      Category: {upgrade.change_category.value}")
            print(f"      Forbidden check: {'PASS' if upgrade.forbidden_check_passed else 'FAIL'}")
            print(f"      Requires approval: {'YES' if upgrade.requires_approval else 'NO'}")
            print(f"      Description: {upgrade.description[:60]}...")


async def example_approval_workflow():
    """
    Example 9: Approval Workflow for Restricted Changes
    Governance threshold changes require manual approval
    """
    print("\n" + "=" * 70)
    print("Example 9: Approval Workflow")
    print("=" * 70)
    
    governance = create_meta_agent_governance_layer()
    
    print("\n  Change categories and requirements:")
    
    categories = [
        ("PARAMETER_TUNING", ChangeCategory.SAFE, "No approval needed"),
        ("CONFIG_UPDATE", ChangeCategory.SAFE, "No approval needed"),
        ("BEHAVIOR_TEMPLATE", ChangeCategory.SAFE, "No approval needed"),
        ("GOVERNANCE_THRESHOLD", ChangeCategory.RESTRICTED, "Requires manual approval"),
        ("LIVE_EXECUTION_LOGIC", ChangeCategory.FORBIDDEN, "Automatically blocked"),
        ("RISK_CONTROL", ChangeCategory.FORBIDDEN, "Automatically blocked"),
        ("CAPITAL_LIMIT", ChangeCategory.FORBIDDEN, "Automatically blocked"),
    ]
    
    for change_type, category, requirement in categories:
        print(f"\n    {change_type}")
        print(f"      Category: {category.value}")
        print(f"      Requirement: {requirement}")
    
    print("\n  Simulating approval request...")
    
    # Create a mock restricted upgrade
    from trading_bot.meta_governance import CandidateUpgrade
    
    upgrade = CandidateUpgrade(
        upgrade_id="test_restricted_001",
        target_agent_id="signal_agent_001",
        target_agent_type=AgentType.SIGNAL_AGENT,
        change_type=ChangeType.GOVERNANCE_THRESHOLD,
        change_category=ChangeCategory.RESTRICTED,
        description="Adjust validation threshold for faster signals",
        proposed_changes={'threshold': 0.75},
        is_forbidden=False,
        forbidden_check_passed=True,
        requires_approval=True,
        approval_status='pending',
        generated_at=datetime.utcnow(),
        generation_method='manual',
        confidence_score=0.8,
        validation_status='pending',
        validation_results=None,
        promotion_status='pending',
        promoted_at=None,
        rolled_back_at=None
    )
    
    governance.pending_approvals[upgrade.upgrade_id] = upgrade
    
    print(f"\n    Upgrade ID: {upgrade.upgrade_id}")
    print(f"    Status: {upgrade.approval_status}")
    print(f"    Requires approval: YES")
    print(f"    Would modify: Governance threshold")
    
    print("\n    ⏳ Waiting for manual approval...")
    print("    (In production, this would notify human reviewers)")


async def example_complete_governance_workflow():
    """
    Example 10: Complete Governance Workflow
    Full cycle from detection to promotion
    """
    print("\n" + "=" * 70)
    print("Example 10: Complete Governance Workflow")
    print("=" * 70)
    
    print("\n🚀 Starting complete meta-agent governance workflow\n")
    
    governance = create_meta_agent_governance_layer()
    
    print("PHASE 1: Continuous Monitoring")
    print("  - Monitoring all agents across the trading bot")
    print("  - Tracking: latency, errors, economic contribution, robustness")
    print("  - Checking for contaminated labels...")
    
    await governance._monitor_all_agents()
    print(f"  ✓ Monitored {len(governance.agent_performance)} agents")
    
    print("\nPHASE 2: Underperformance Detection")
    print("  - Analyzing agent performance metrics...")
    print("  - Identifying agents with issues...")
    
    await governance._detect_underperformance()
    print(f"  ✓ Found {len(governance.underperforming_agents)} underperforming agents")
    
    print("\nPHASE 3: Safe Upgrade Generation")
    print("  - Checking for contaminated labels...")
    print("  - Validating sample sizes...")
    print("  - Scanning for forbidden patterns...")
    print("  - Generating only safe improvements...")
    
    await governance._generate_safe_upgrades()
    print(f"  ✓ Generated {len(governance.candidate_upgrades)} safe upgrades")
    
    # Show blocked attempts
    if governance.forbidden_attempts:
        print(f"  🚫 Blocked {len(governance.forbidden_attempts)} forbidden change attempts")
    
    print("\nPHASE 4: Offline Validation")
    print("  - Testing in sandbox environment...")
    print("  - Running stress tests...")
    print("  - Measuring across market regimes...")
    print("  - Checking: Robustness, Safety, Economic Value...")
    
    await governance._validate_upgrades()
    
    passed = sum(1 for u in governance.candidate_upgrades.values() if u.validation_status == 'passed')
    failed = sum(1 for u in governance.candidate_upgrades.values() if u.validation_status == 'failed')
    
    print(f"  ✓ Validation complete")
    print(f"    Passed: {passed}")
    print(f"    Failed: {failed}")
    
    print("\nPHASE 5: Three-Criteria Promotion Gate")
    print("  - Checking robustness improvement...")
    print("  - Verifying safety metrics...")
    print("  - Confirming economic value...")
    print("  - ALL THREE must pass...")
    
    await governance._promote_validated_upgrades()
    
    promoted = sum(1 for u in governance.candidate_upgrades.values() if u.promotion_status == 'promoted')
    print(f"  ✓ Promoted {promoted} upgrades to production")
    
    print("\nPHASE 6: Ongoing Monitoring")
    print("  - Tracking promoted upgrade performance...")
    print("  - Ready to rollback if issues detected...")
    print("  - Continuously scanning for new underperformance...")
    
    print("\n✓ Complete governance workflow finished")
    
    print("\n" + "=" * 70)
    print("SAFETY SUMMARY")
    print("=" * 70)
    print(f"  Forbidden attempts blocked: {len(governance.forbidden_attempts)}")
    print(f"  Contaminated agents flagged: {len([p for p in governance.agent_performance.values() if p.contamination_ratio > 0.02])}")
    print(f"  Sample size violations: {len([p for p in governance.agent_performance.values() if p.trades_count < 1000])}")
    print(f"  Upgrades promoted: {promoted}")
    print(f"  Upgrades rejected: {failed}")


async def run_all_examples():
    """Run all examples"""
    await example_initialization()
    await example_agent_monitoring()
    await example_underperformance_detection()
    await example_forbidden_change_blocking()
    await example_contaminated_label_detection()
    await example_sample_size_validation()
    await example_three_criteria_promotion()
    await example_safe_upgrade_generation()
    await example_approval_workflow()
    await example_complete_governance_workflow()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\n🛡️ Meta-Agent Governance Layer enforces:")
    print("   ✓ Monitoring of ALL agents in the trading bot")
    print("   ✓ Detection of underperforming behavior")
    print("   ✓ BLOCKING of forbidden changes:")
    print("     - Live execution logic modifications")
    print("     - Risk control changes")
    print("     - Capital limit alterations")
    print("   ✓ APPROVAL workflow for governance threshold changes")
    print("   ✓ NO learning from contaminated labels")
    print("   ✓ NO promotion based on tiny sample wins")
    print("   ✓ Three-criteria promotion gate:")
    print("     - ROBUSTNESS: Must improve across regimes")
    print("     - SAFETY: Must not increase risk")
    print("     - ECONOMIC VALUE: Must be profitable")
    print("\n   The system ONLY promotes improvements that increase")
    print("   robustness, safety, and economic value.")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
