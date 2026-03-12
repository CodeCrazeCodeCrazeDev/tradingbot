"""
Self-Healing AI Validator System Demo

Demonstrates the comprehensive validation system that addresses 1000+ critical questions
for trading bot robustness, reliability, and safety.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.self_healing_ai import quick_start, get_orchestrator
from trading_bot.self_healing_ai.core import (
    ValidationSeverity, ValidationCategory, SystemState, SystemHealth
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_validation():
    """Demo basic validation run."""
    print("\n" + "="*80)
    print("SELF-HEALING AI VALIDATOR SYSTEM DEMO")
    print("Addressing 1000+ Critical Questions for Trading Bot Robustness")
    print("="*80 + "\n")
    
    # Initialize orchestrator
    print("Initializing Self-Healing AI Orchestrator...")
    orchestrator = await quick_start({
        'auto_remediate': True,
        'validation_interval_seconds': 60
    })
    
    # Show validator summary
    print("\n--- VALIDATOR SUMMARY ---")
    summary = orchestrator.get_validator_summary()
    total_checks = 0
    for name, info in summary.items():
        print(f"  {name}: {info['checks_count']} checks, {info['remediations_count']} remediations")
        total_checks += info['checks_count']
    print(f"\nTotal: {len(summary)} validators, {total_checks}+ validation checks")
    
    # Show immutable limits
    print("\n--- IMMUTABLE SAFETY LIMITS ---")
    limits = orchestrator.get_immutable_limits()
    for limit, value in limits.items():
        if isinstance(value, float) and value < 1:
            print(f"  {limit}: {value*100:.1f}%")
        else:
            print(f"  {limit}: {value}")
    
    # Run full validation
    print("\n--- RUNNING FULL VALIDATION ---")
    report = await orchestrator.run_full_validation()
    
    # Display results
    print(f"\nValidation Report ID: {report.report_id}")
    print(f"Generated At: {report.generated_at}")
    print(f"Execution Time: {report.execution_time_ms:.1f}ms")
    print(f"\nSystem Health: {report.system_health.value.upper()}")
    print(f"Total Checks: {report.total_checks}")
    print(f"Passed: {report.passed_checks}")
    print(f"Failed: {report.failed_checks}")
    print(f"Pass Rate: {report.passed_checks/report.total_checks*100:.1f}%" if report.total_checks > 0 else "N/A")
    
    # Category scores
    print("\n--- CATEGORY SCORES ---")
    for category, score in sorted(report.category_scores.items(), key=lambda x: x[1]):
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        status = "✓" if score >= 0.9 else "⚠" if score >= 0.7 else "✗"
        print(f"  {status} {category:25} [{bar}] {score*100:.0f}%")
    
    # Issues by severity
    if report.issues:
        print("\n--- ISSUES BY SEVERITY ---")
        by_severity = {}
        for issue in report.issues:
            sev = issue.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_severity.get(sev, 0)
            if count > 0:
                icon = "🔴" if sev == 'critical' else "🟠" if sev == 'high' else "🟡" if sev == 'medium' else "🟢"
                print(f"  {icon} {sev.upper()}: {count}")
        
        # Show critical issues
        critical = report.get_critical_issues()
        if critical:
            print("\n--- CRITICAL ISSUES (Require Immediate Attention) ---")
            for issue in critical[:5]:
                print(f"\n  [{issue.issue_id[:8]}] {issue.title}")
                print(f"    Category: {issue.category.value}")
                print(f"    Question ID: Q{issue.question_id}")
                print(f"    Description: {issue.description[:100]}...")
                print(f"    Affected: {', '.join(issue.affected_components)}")
                if issue.remediation_available:
                    print(f"    Remediation: {issue.remediation_action}")
                    print(f"    Auto-remediate: {'Yes' if issue.auto_remediate else 'No'}")
    
    # Remediations
    if report.remediations:
        print(f"\n--- REMEDIATIONS PERFORMED: {len(report.remediations)} ---")
        for rem in report.remediations[:5]:
            print(f"  [{rem.action_id[:8]}] {rem.action_type}: {rem.status.value}")
    
    # Recommendations
    if report.recommendations:
        print("\n--- RECOMMENDATIONS ---")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
    
    return orchestrator, report


async def demo_category_validation(orchestrator):
    """Demo validation of specific categories."""
    print("\n" + "="*80)
    print("CATEGORY-SPECIFIC VALIDATION")
    print("="*80 + "\n")
    
    categories = ['risk', 'security', 'kill_switch']
    
    for category in categories:
        print(f"\n--- Validating: {category.upper()} ---")
        issues = await orchestrator.validate_category(category)
        
        if issues:
            print(f"  Found {len(issues)} issues:")
            for issue in issues[:3]:
                print(f"    - [{issue.severity.value}] {issue.title}")
        else:
            print("  ✓ No issues found")


async def demo_state_update(orchestrator):
    """Demo state updates and re-validation."""
    print("\n" + "="*80)
    print("STATE UPDATE AND RE-VALIDATION")
    print("="*80 + "\n")
    
    # Update state with simulated data
    print("Updating system state with simulated data...")
    orchestrator.update_state(
        capital=100000,
        equity=98000,
        drawdown=0.02,
        daily_pnl=-500,
        active_strategies=['momentum', 'mean_reversion'],
        connected_brokers=['binance', 'alpaca'],
        positions={
            'BTCUSDT': {'size': 0.5, 'risk_percent': 0.01, 'size_percent': 0.05},
            'ETHUSDT': {'size': 2.0, 'risk_percent': 0.015, 'size_percent': 0.03},
        },
        error_counts={
            'stale_reference': 0,
            'rate_limit': 2,
            'missing_data': 5,
        },
        latency_metrics={
            'e2e_latency_ms': 45,
            'signal_to_ack_ms': 30,
            'network_ms': 10,
        }
    )
    
    # Get current state
    state = orchestrator.get_state()
    print(f"\nCurrent State:")
    print(f"  Capital: ${state.capital:,.0f}")
    print(f"  Equity: ${state.equity:,.0f}")
    print(f"  Drawdown: {state.drawdown*100:.1f}%")
    print(f"  Daily P&L: ${state.daily_pnl:,.0f}")
    print(f"  Active Strategies: {', '.join(state.active_strategies)}")
    print(f"  Positions: {len(state.positions)}")
    
    # Re-run validation
    print("\nRe-running validation with updated state...")
    report = await orchestrator.run_full_validation()
    
    print(f"\nUpdated Health: {report.system_health.value.upper()}")
    print(f"Issues: {len(report.issues)}")


async def main():
    """Run all demos."""
    try:
        # Basic validation demo
        orchestrator, report = await demo_basic_validation()
        
        # Category validation demo
        await demo_category_validation(orchestrator)
        
        # State update demo
        await demo_state_update(orchestrator)
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        print("\nThe Self-Healing AI Validator System provides:")
        print("  • 16 validator categories")
        print("  • 1000+ critical questions addressed")
        print("  • Automatic issue detection")
        print("  • Auto-remediation capabilities")
        print("  • Continuous monitoring support")
        print("  • Immutable safety limits")
        print("\nUsage in your code:")
        print("  from trading_bot.self_healing_ai import quick_start")
        print("  orchestrator = await quick_start()")
        print("  report = await orchestrator.run_full_validation()")
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
