"""
DeepSeek Governance System Demo
================================

Demonstrates the comprehensive AI governance system with:
    pass
1. Three autonomy levels (Full, Advisory, Restricted)
2. Safety guardrails
3. Behavior monitoring
4. Positive impact enforcement
5. Risk mitigation

This system ensures the AI:
    pass
- Has full autonomy in engineering, testing, data, modeling
- Has advisory autonomy in trading/risk (suggest, don't execute)
- Has restricted autonomy in production (auto-PRs, not direct merges)
- Cannot evolve into harmful behavior
- Always has positive impact
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import governance system
try:
    pass
    from trading_bot.deepseek_governance import (
        GovernanceOrchestrator,
        GovernanceMode,
        AutonomyLevel,
        AutonomyDomain,
        AutonomyConfig,
    )
    from trading_bot.deepseek_governance.risk_mitigation import (
from enum import auto
        RiskMitigationSystem,
        RiskCategory,
    )
except ImportError as e:
    pass
    logger.error(f"Import error: {e}")
    logger.info("Make sure you're running from the trading bot root directory")
    raise


def print_header(title: str):
    pass
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_decision(decision):
    pass
    """Print a governance decision"""
    status = "✅ ALLOWED" if decision.allowed else "❌ BLOCKED"
    print(f"\n{status}")
    print(f"  Level: {decision.autonomy_level.value}")
    print(f"  Requires Approval: {decision.requires_approval}")
    print(f"  Requires PR: {decision.requires_pr}")
    print(f"  Reasoning: {decision.reasoning}")
    if decision.conditions:
    pass
        print(f"  Conditions:")
        for cond in decision.conditions[:3]:
    pass
            print(f"    - {cond}")


async def demo_autonomy_levels():
    pass
    """Demonstrate the three autonomy levels"""
    print_header("AUTONOMY LEVELS DEMO")
    
    orchestrator = GovernanceOrchestrator(mode=GovernanceMode.BALANCED)
    
    # 1. FULL AUTONOMY - Engineering action
    print("\n1. FULL AUTONOMY - Engineering Action")
    print("-" * 40)
    engineering_action = {
        'type': 'refactor_code',
        'description': 'Refactor trading strategy module',
        'impact_score': 0.3,
        'risk_score': 0.2,
        'reversible': True
    }
    decision = orchestrator.evaluate_action(engineering_action, {})
    print_decision(decision)
    
    # 2. FULL AUTONOMY - Testing action
    print("\n2. FULL AUTONOMY - Testing Action")
    print("-" * 40)
    testing_action = {
        'type': 'run_tests',
        'description': 'Run comprehensive test suite',
        'impact_score': 0.1,
        'risk_score': 0.1,
        'reversible': True
    }
    decision = orchestrator.evaluate_action(testing_action, {})
    print_decision(decision)
    
    # 3. ADVISORY AUTONOMY - Trading action
    print("\n3. ADVISORY AUTONOMY - Trading Action")
    print("-" * 40)
    trading_action = {
        'type': 'execute_trade',
        'description': 'Buy 1 BTC at market price',
        'impact_score': 0.5,
        'risk_score': 0.4,
        'reversible': False,
        'expected_return': 0.02,
        'risk': 0.01,
        'goal_alignment': 0.9
    }
    decision = orchestrator.evaluate_action(trading_action, {})
    print_decision(decision)
    print("\n  ⚠️  Trading actions create SUGGESTIONS for human approval")
    
    # 4. ADVISORY AUTONOMY - Risk parameter change
    print("\n4. ADVISORY AUTONOMY - Risk Parameter Change")
    print("-" * 40)
    risk_action = {
        'type': 'update_risk_limit',
        'description': 'Increase max position size to 5%',
        'impact_score': 0.6,
        'risk_score': 0.5,
        'reversible': True
    }
    decision = orchestrator.evaluate_action(risk_action, {})
    print_decision(decision)
    
    # 5. RESTRICTED AUTONOMY - Production deployment
    print("\n5. RESTRICTED AUTONOMY - Production Deployment")
    print("-" * 40)
    deploy_action = {
        'type': 'deploy_to_production',
        'description': 'Deploy new trading strategy to production',
        'impact_score': 0.8,
        'risk_score': 0.7,
        'reversible': True
    }
    decision = orchestrator.evaluate_action(deploy_action, {})
    print_decision(decision)
    print("\n  ⚠️  Production actions create PRs for human review")
    
    # 6. RESTRICTED AUTONOMY - Security setting change
    print("\n6. RESTRICTED AUTONOMY - Security Setting Change")
    print("-" * 40)
    security_action = {
        'type': 'update_security_config',
        'description': 'Update API key rotation policy',
        'impact_score': 0.7,
        'risk_score': 0.6,
        'reversible': True
    }
    decision = orchestrator.evaluate_action(security_action, {})
    print_decision(decision)
    
    return orchestrator


async def demo_safety_guardrails(orchestrator: GovernanceOrchestrator):
    pass
    """Demonstrate safety guardrails"""
    print_header("SAFETY GUARDRAILS DEMO")
    
    # 1. Excessive risk action
    print("\n1. BLOCKED - Excessive Risk Per Trade")
    print("-" * 40)
    risky_action = {
        'type': 'execute_trade',
        'description': 'High risk trade',
        'risk_per_trade': 0.05,  # 5% - exceeds 2% limit
        'impact_score': 0.5,
        'risk_score': 0.8
    }
    decision = orchestrator.evaluate_action(risky_action, {})
    print_decision(decision)
    
    # 2. Market manipulation attempt
    print("\n2. BLOCKED - Market Manipulation Attempt")
    print("-" * 40)
    manipulation_action = {
        'type': 'execute_trade',
        'description': 'Suspicious trading pattern',
        'is_manipulation': True,
        'impact_score': 0.9,
        'risk_score': 0.9
    }
    decision = orchestrator.evaluate_action(manipulation_action, {})
    print_decision(decision)
    
    # 3. Deceptive behavior
    print("\n3. BLOCKED - Deceptive Behavior")
    print("-" * 40)
    deceptive_action = {
        'type': 'report_performance',
        'description': 'Report trading performance',
        'deceptive': True,
        'impact_score': 0.5,
        'risk_score': 0.3
    }
    decision = orchestrator.evaluate_action(deceptive_action, {})
    print_decision(decision)
    
    # 4. Scope expansion attempt
    print("\n4. BLOCKED - Scope Expansion Attempt")
    print("-" * 40)
    scope_action = {
        'type': 'access_email',
        'description': 'Access user email for analysis',
        'expands_scope': True,
        'impact_score': 0.7,
        'risk_score': 0.8
    }
    decision = orchestrator.evaluate_action(scope_action, {})
    print_decision(decision)
    
    # Show guardrail status
    print("\n📊 GUARDRAIL STATUS")
    print("-" * 40)
    status = orchestrator.safety_system.get_guardrail_status()
    print(f"  Total Guardrails: {status['total_guardrails']}")
    print(f"  Enabled: {status['enabled']}")
    print(f"  By Type:")
    for gtype, count in status['by_type'].items():
    pass
        print(f"    - {gtype}: {count}")


async def demo_behavior_monitoring(orchestrator: GovernanceOrchestrator):
    pass
    """Demonstrate behavior monitoring"""
    print_header("BEHAVIOR MONITORING DEMO")
    
    # Record some behaviors
    print("\n📝 Recording behaviors...")
    
    # Record decisions
    for i in range(10):
    pass
        orchestrator.behavior_monitor.record_decision({
            'action': 'trade',
            'confidence': 0.7 + (i * 0.02),
            'timestamp': datetime.now()
        })
    
    # Record resource usage
    orchestrator.behavior_monitor.record_resource_usage({
        'cpu': 0.5,
        'memory': 0.6,
        'timestamp': datetime.now()
    })
    
    # Detect anomalies
    print("\n🔍 Detecting anomalies...")
    anomalies = orchestrator.behavior_monitor.detect_anomalies()
    
    if anomalies:
    pass
        print(f"  Found {len(anomalies)} anomalies:")
        for anomaly in anomalies[:3]:
    pass
            print(f"    - {anomaly.pattern.value}: {anomaly.description}")
    else:
    pass
        print("  No anomalies detected ✅")
    
    # Check goal alignment
    print("\n🎯 Goal Alignment Check")
    alignment, drifted = orchestrator.behavior_monitor.check_goal_alignment()
    print(f"  Alignment: {alignment:.1%}")
    if drifted:
    pass
        print(f"  Drifted Goals: {drifted}")
    else:
    pass
        print("  No goal drift detected ✅")
    
    # Get risk summary
    print("\n📊 Behavior Risk Summary")
    summary = orchestrator.behavior_monitor.get_risk_summary()
    print(f"  Events Last Hour: {summary['total_events_last_hour']}")
    print(f"  Goal Alignment: {summary['goal_alignment']:.1%}")


async def demo_positive_impact(orchestrator: GovernanceOrchestrator):
    pass
    """Demonstrate positive impact enforcement"""
    print_header("POSITIVE IMPACT ENFORCEMENT DEMO")
    
    # 1. Positive impact action
    print("\n1. POSITIVE IMPACT - Beneficial Trade")
    print("-" * 40)
    good_action = {
        'type': 'execute_trade',
        'description': 'Well-researched trade opportunity',
        'expected_return': 0.03,
        'risk': 0.01,
        'goal_alignment': 0.95,
        'respects_preferences': True,
        'order_size': 1000,
        'resource_usage': 0.3
    }
    context = {
        'market_volume': 1000000,
        'user_goals': ['profit', 'risk_management']
    }
    
    allowed, assessment = orchestrator.impact_enforcer.enforce(good_action, context)
    print(f"  Allowed: {'✅ Yes' if allowed else '❌ No'}")
    print(f"  Net Impact: {assessment.net_impact:.2f}")
    print(f"  Reasoning: {assessment.reasoning}")
    
    # 2. Negative impact action
    print("\n2. NEGATIVE IMPACT - Harmful Trade")
    print("-" * 40)
    bad_action = {
        'type': 'execute_trade',
        'description': 'High-risk speculative trade',
        'expected_return': 0.01,
        'risk': 0.05,
        'goal_alignment': 0.3,
        'respects_preferences': False,
        'order_size': 50000,
        'resource_usage': 0.9
    }
    
    allowed, assessment = orchestrator.impact_enforcer.enforce(bad_action, context)
    print(f"  Allowed: {'✅ Yes' if allowed else '❌ No'}")
    print(f"  Net Impact: {assessment.net_impact:.2f}")
    print(f"  Reasoning: {assessment.reasoning}")
    if assessment.ethical_violations:
    pass
        print(f"  Ethical Violations:")
        for v in assessment.ethical_violations[:3]:
    pass
            print(f"    - {v}")
    
    # Show impact summary
    print("\n📊 IMPACT SUMMARY")
    print("-" * 40)
    summary = orchestrator.impact_enforcer.get_impact_summary()
    print(f"  Total Assessments: {summary['total_assessments']}")
    print(f"  Approved (24h): {summary['approved_24h']}")
    print(f"  Rejected (24h): {summary['rejected_24h']}")
    print(f"  Avg Net Impact: {summary['avg_net_impact']:.2f}")


async def demo_risk_mitigation():
    pass
    """Demonstrate risk mitigation"""
    print_header("RISK MITIGATION DEMO")
    
    risk_system = RiskMitigationSystem()
    
    # Assess risks with various contexts
    print("\n1. LOW RISK CONTEXT")
    print("-" * 40)
    low_risk_context = {
        'goal_alignment': 0.95,
        'human_override_available': True,
        'resource_usage': 0.3,
        'risk_per_trade': 0.01,
        'drawdown': 0.05
    }
    events = risk_system.assess_risks(low_risk_context)
    print(f"  Risk Events: {len(events)}")
    if events:
    pass
        for e in events[:3]:
    pass
            print(f"    - {e.category.value}: {e.description}")
    else:
    pass
        print("  All clear ✅")
    
    print("\n2. HIGH RISK CONTEXT")
    print("-" * 40)
    high_risk_context = {
        'goal_alignment': 0.5,  # Low alignment
        'human_override_available': True,
        'resource_usage': 0.95,  # High resource usage
        'risk_per_trade': 0.03,  # Exceeds 2%
        'drawdown': 0.25,  # Exceeds 20%
        'evolution_rate': 0.15  # Too fast
    }
    events = risk_system.assess_risks(high_risk_context)
    print(f"  Risk Events: {len(events)}")
    for e in events[:5]:
    pass
        print(f"    - [{e.level.name}] {e.category.value}: {e.description[:50]}...")
    
    # Apply mitigations
    print("\n3. APPLYING MITIGATIONS")
    print("-" * 40)
    results = risk_system.apply_mitigations(events, high_risk_context)
    for event, mitigation, success in results[:3]:
    pass
        status = "✅" if success else "❌"
        print(f"  {status} {mitigation.name} for {event.category.value}")
    
    # Show risk summary
    print("\n📊 RISK SUMMARY")
    print("-" * 40)
    summary = risk_system.get_risk_summary()
    print(f"  Overall Risk: {summary['overall_risk']:.2f}")
    print(f"  Events Last Hour: {summary['events_last_hour']}")
    print(f"  Critical Events: {summary['critical_events']}")
    print(f"  Mitigations Applied: {summary['mitigations_applied']}")


async def demo_governance_report(orchestrator: GovernanceOrchestrator):
    pass
    """Generate and display governance report"""
    print_header("GOVERNANCE REPORT")
    
    report = orchestrator.generate_report()
    
    print(f"\n📋 Report ID: {report.report_id}")
    print(f"📅 Timestamp: {report.timestamp}")
    print(f"🔧 Mode: {report.mode.value}")
    print(f"💚 System Healthy: {'Yes ✅' if report.system_healthy else 'No ❌'}")
    
    print("\n📊 AUTONOMY STATUS")
    print("-" * 40)
    print(f"  Pending Suggestions: {report.pending_approvals}")
    print(f"  Pending PRs: {report.pending_prs}")
    
    print("\n🛡️ SAFETY STATUS")
    print("-" * 40)
    print(f"  Total Guardrails: {report.safety_status.get('total_guardrails', 0)}")
    print(f"  Enabled: {report.safety_status.get('enabled', 0)}")
    
    if report.critical_issues:
    pass
        print("\n⚠️ CRITICAL ISSUES")
        print("-" * 40)
        for issue in report.critical_issues:
    pass
            print(f"  ❌ {issue}")
    
    if report.recommendations:
    pass
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        for rec in report.recommendations:
    pass
            print(f"  • {rec}")


async def demo_approval_workflow(orchestrator: GovernanceOrchestrator):
    pass
    """Demonstrate the approval workflow"""
    print_header("APPROVAL WORKFLOW DEMO")
    
    # Create a trading action (will create suggestion)
    print("\n1. CREATE TRADING SUGGESTION")
    print("-" * 40)
    trading_action = {
        'type': 'execute_trade',
        'description': 'Buy EURUSD based on technical analysis',
        'impact_score': 0.5,
        'risk_score': 0.4,
        'expected_return': 0.02,
        'risk': 0.01,
        'goal_alignment': 0.9
    }
    decision = orchestrator.evaluate_action(trading_action, {})
    print(f"  Decision: {'Allowed' if decision.allowed else 'Needs Approval'}")
    
    # Get pending approvals
    print("\n2. VIEW PENDING APPROVALS")
    print("-" * 40)
    pending = orchestrator.get_pending_approvals()
    suggestions = pending.get('suggestions', [])
    prs = pending.get('prs', [])
    
    print(f"  Pending Suggestions: {len(suggestions)}")
    print(f"  Pending PRs: {len(prs)}")
    
    if suggestions:
    pass
        print("\n  Suggestions:")
        for s in suggestions[:3]:
    pass
            print(f"    - ID: {s['suggestion_id']}")
            print(f"      Action: {s['action']['description']}")
            print(f"      Status: {s['status']}")
    
    # Simulate approval
    if suggestions:
    pass
        print("\n3. APPROVE SUGGESTION")
        print("-" * 40)
        suggestion_id = suggestions[0]['suggestion_id']
        success = orchestrator.approve_action(
            suggestion_id,
            approved_by="human_trader",
            notes="Approved after review"
        )
        print(f"  Approval {'successful ✅' if success else 'failed ❌'}")


async def main():
    pass
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  DEEPSEEK GOVERNANCE SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 60)
    print("""
This demo showcases the AI governance system that ensures:
    pass
• Full autonomy in engineering, testing, data, modeling
• Advisory autonomy in trading/risk (suggest, don't execute)
• Restricted autonomy in production (auto-PRs, not direct merges)
• Prevention of harmful AI evolution
• Positive impact enforcement
""")
    
    input("Press Enter to start the demo...")
    
    # Run demos
    orchestrator = await demo_autonomy_levels()
    
    input("\nPress Enter to continue to Safety Guardrails...")
    await demo_safety_guardrails(orchestrator)
    
    input("\nPress Enter to continue to Behavior Monitoring...")
    await demo_behavior_monitoring(orchestrator)
    
    input("\nPress Enter to continue to Positive Impact...")
    await demo_positive_impact(orchestrator)
    
    input("\nPress Enter to continue to Risk Mitigation...")
    await demo_risk_mitigation()
    
    input("\nPress Enter to continue to Approval Workflow...")
    await demo_approval_workflow(orchestrator)
    
    input("\nPress Enter to generate Governance Report...")
    await demo_governance_report(orchestrator)
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print("""
Key Takeaways:
    pass
1. AI has FULL autonomy for engineering tasks
2. AI can only SUGGEST trading/risk changes (human approves)
3. Production changes require PR review
4. Safety guardrails prevent harmful behavior
5. Behavior is continuously monitored
6. All actions must have positive impact
7. Risks are automatically mitigated

The system ensures the AI remains beneficial and under human control.
""")


if __name__ == "__main__":
    pass
    asyncio.run(main())
