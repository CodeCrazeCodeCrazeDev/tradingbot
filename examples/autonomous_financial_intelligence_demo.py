"""
Autonomous Financial Intelligence Infrastructure Demo
=======================================================

Demonstrates the complete self-coordinating AI system:
1. Core Production System (Immutable)
2. Sandbox Execution Environment
3. Compute Budget Controller
4. Experiment Registry
5. Data Integrity Firewall
6. Code Safety Scanner
7. Promotion System
8. Market Opportunity Discovery
9. Self-Programming Proposer

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_core_production_system():
    """Demo 1: Core Production System (Immutable)"""
    print("\n" + "=" * 70)
    print("DEMO 1: CORE PRODUCTION SYSTEM (IMMUTABLE)")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import CoreProductionSystem, ProductionConfig
    
    # Create production system with strict limits
    config = ProductionConfig(
        max_position_size_pct=0.10,
        max_daily_loss_pct=0.05,
        max_drawdown_pct=0.15,
        max_leverage=2.0,
        max_trades_per_day=100,
    )
    
    production = CoreProductionSystem(config)
    await production.initialize()
    
    print("\n✅ Core Production System initialized")
    print(f"   System ID: {config.system_id}")
    print(f"   Config Hash: {config.get_hash()[:16]}...")
    
    # Start the system
    production.start()
    print("\n✅ Production system started")
    
    # Show status
    status = production.get_status()
    print(f"\n📊 Production Status:")
    print(f"   State: {status['state']}")
    print(f"   Protected Components: {status['protected_components']}")
    print(f"   Modification Attempts Blocked: {status['modification_attempts']}")
    
    # Verify integrity
    integrity = production.verify_system_integrity()
    print(f"\n🔒 Integrity Check:")
    print(f"   All Valid: {integrity['all_valid']}")
    for comp, info in integrity['components'].items():
        print(f"   - {comp}: {info['protection_level']} ({'✓' if info['is_valid'] else '✗'})")
    
    # Pause system
    production.pause("Demo complete", "demo_script")
    print("\n⏸️ Production system paused")


async def demo_sandbox_executor():
    """Demo 2: Sandbox Execution Environment"""
    print("\n" + "=" * 70)
    print("DEMO 2: SANDBOX EXECUTION ENVIRONMENT")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import SandboxExecutor, SandboxConfig
    
    # Create sandbox with strict limits
    config = SandboxConfig(
        max_cpu_time_seconds=60,
        max_memory_mb=512,
        allow_network=False,
        allow_subprocess=False,
    )
    
    sandbox = SandboxExecutor(config)
    
    print("\n✅ Sandbox Executor initialized")
    print(f"   Max CPU Time: {config.max_cpu_time_seconds}s")
    print(f"   Max Memory: {config.max_memory_mb}MB")
    print(f"   Network: {'Allowed' if config.allow_network else 'Blocked'}")
    
    # Test safe code
    safe_code = '''
import math

def calculate_indicator(prices):
    """Calculate simple moving average."""
    if len(prices) < 20:
        return None
    return sum(prices[-20:]) / 20

# Test
prices = [100 + i * 0.5 for i in range(50)]
result = calculate_indicator(prices)
print(f"SMA Result: {result}")
metrics['sma_value'] = result
'''
    
    print("\n🔬 Executing safe code in sandbox...")
    result = await sandbox.execute(safe_code)
    
    print(f"\n📊 Execution Result:")
    print(f"   Status: {result.status.name}")
    print(f"   Success: {result.is_success}")
    print(f"   Wall Time: {result.wall_time_used:.2f}s")
    print(f"   Memory Peak: {result.memory_peak_mb:.1f}MB")
    if result.stdout:
        print(f"   Output: {result.stdout.strip()}")
    
    # Test dangerous code (should be blocked)
    dangerous_code = '''
import os
os.system("echo dangerous")
'''
    
    print("\n🚫 Attempting to execute dangerous code...")
    result = await sandbox.execute(dangerous_code)
    
    print(f"\n📊 Execution Result:")
    print(f"   Status: {result.status.name}")
    print(f"   Blocked: {not result.is_success}")
    if result.security_violations:
        print(f"   Violations: {result.security_violations}")
    
    # Show statistics
    stats = sandbox.get_statistics()
    print(f"\n📈 Sandbox Statistics:")
    print(f"   Total Executions: {stats['total_executions']}")
    print(f"   Completed: {stats['completed_executions']}")
    print(f"   Security Violations: {stats['security_violations']}")


async def demo_code_safety_scanner():
    """Demo 3: Code Safety Scanner"""
    print("\n" + "=" * 70)
    print("DEMO 3: CODE SAFETY SCANNER")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import CodeSafetyScanner
    
    scanner = CodeSafetyScanner()
    
    print("\n✅ Code Safety Scanner initialized")
    
    # Scan safe code
    safe_code = '''
import numpy as np
import pandas as pd

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index."""
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
'''
    
    print("\n🔍 Scanning safe code...")
    result = scanner.scan(safe_code)
    
    print(f"\n📊 Scan Result:")
    print(f"   Security Level: {result.security_level.value}")
    print(f"   Is Safe: {result.is_safe}")
    print(f"   Can Execute: {result.can_execute}")
    print(f"   Lines of Code: {result.lines_of_code}")
    print(f"   Complexity Score: {result.complexity_score:.1f}")
    print(f"   Issues Found: {len(result.issues)}")
    
    # Scan dangerous code
    dangerous_code = '''
import os
import subprocess

def dangerous_function():
    os.system("rm -rf /")
    subprocess.call(["curl", "http://evil.com"])
    exec("malicious_code")
    eval(user_input)
'''
    
    print("\n🔍 Scanning dangerous code...")
    result = scanner.scan(dangerous_code)
    
    print(f"\n📊 Scan Result:")
    print(f"   Security Level: {result.security_level.value}")
    print(f"   Is Safe: {result.is_safe}")
    print(f"   Can Execute: {result.can_execute}")
    print(f"   Issues Found: {len(result.issues)}")
    print(f"   Blocked Imports: {result.blocked_imports}")
    print(f"   Blocked Functions: {result.blocked_functions}")
    
    if result.issues:
        print(f"\n⚠️ Security Issues:")
        for issue in result.issues[:5]:
            print(f"   - [{issue.severity.value}] {issue.description}")


async def demo_experiment_registry():
    """Demo 4: Experiment Registry"""
    print("\n" + "=" * 70)
    print("DEMO 4: EXPERIMENT REGISTRY")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import (
        ExperimentRegistry, ExperimentType, ExperimentCategory, ExperimentMetrics
    )
    
    registry = ExperimentRegistry(storage_path="demo_experiments")
    
    print("\n✅ Experiment Registry initialized")
    
    # Register an experiment
    experiment = await registry.register_experiment(
        name="Enhanced Momentum Strategy",
        description="Momentum strategy with volatility filter",
        experiment_type=ExperimentType.STRATEGY,
        category=ExperimentCategory.ALPHA_GENERATION,
        code='''
def momentum_strategy(data, fast=10, slow=30):
    fast_ma = data['close'].rolling(fast).mean()
    slow_ma = data['close'].rolling(slow).mean()
    return (fast_ma > slow_ma).astype(int)
''',
        config={'fast_period': 10, 'slow_period': 30},
        created_by='self_programmer',
        tags={'momentum', 'trend_following'},
    )
    
    print(f"\n📝 Registered Experiment:")
    print(f"   ID: {experiment.experiment_id}")
    print(f"   Name: {experiment.name}")
    print(f"   Type: {experiment.experiment_type.value}")
    print(f"   Status: {experiment.status.name}")
    
    # Update status to running
    await registry.update_status(experiment.experiment_id, ExperimentStatus.RUNNING)
    print(f"\n▶️ Experiment started")
    
    # Record results
    metrics = ExperimentMetrics(
        sharpe_ratio=1.85,
        sortino_ratio=2.10,
        max_drawdown=0.12,
        win_rate=0.58,
        profit_factor=1.65,
        total_return=0.25,
        execution_time_seconds=45.2,
    )
    
    await registry.record_results(experiment.experiment_id, metrics)
    
    print(f"\n📊 Recorded Results:")
    print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"   Win Rate: {metrics.win_rate:.1%}")
    print(f"   Max Drawdown: {metrics.max_drawdown:.1%}")
    print(f"   Promotion Score: {experiment.promotion_score:.2f}")
    print(f"   Promotion Eligible: {experiment.promotion_eligible}")
    
    # Show statistics
    stats = registry.get_statistics()
    print(f"\n📈 Registry Statistics:")
    print(f"   Total Experiments: {stats['total_experiments']}")
    print(f"   Promotion Candidates: {stats['promotion_candidates']}")


# Need to import ExperimentStatus
from trading_bot.self_coordinating_ai.experiment_registry import ExperimentStatus


async def demo_promotion_system():
    """Demo 5: Promotion System"""
    print("\n" + "=" * 70)
    print("DEMO 5: PROMOTION SYSTEM")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import (
        PromotionSystem, PromotionType, PromotionStatus
    )
    
    promotion = PromotionSystem(storage_path="demo_promotions")
    
    print("\n✅ Promotion System initialized")
    
    # Create promotion request
    request = await promotion.create_promotion_request(
        experiment_id="EXP-demo123",
        promotion_type=PromotionType.STRATEGY,
        code="def strategy(): pass",
        requested_by="self_programmer",
        description="High-performing momentum strategy",
        impact_assessment="Expected 15% improvement in Sharpe ratio",
        rollback_plan="Revert to previous strategy version",
    )
    
    print(f"\n📝 Created Promotion Request:")
    print(f"   ID: {request.request_id}")
    print(f"   Type: {request.promotion_type.value}")
    print(f"   Status: {request.status.name}")
    print(f"   Approval Level: {request.approval_level.name}")
    print(f"   Required Approvals: {request.get_required_approvals()}")
    
    # Submit safety review
    await promotion.submit_safety_review(
        request.request_id,
        passed=True,
        reviewer="code_scanner",
        notes=["All safety checks passed", "No dangerous patterns detected"],
    )
    print(f"\n✅ Safety review passed")
    
    # Submit performance review
    passed, issues = await promotion.submit_performance_review(
        request.request_id,
        metrics={
            'sharpe_ratio': 1.85,
            'win_rate': 0.58,
            'max_drawdown': 0.12,
            'profit_factor': 1.65,
        },
        reviewer="experiment_registry",
    )
    print(f"\n{'✅' if passed else '❌'} Performance review: {'passed' if passed else 'failed'}")
    if issues:
        for issue in issues:
            print(f"   - {issue}")
    
    # Approve
    await promotion.approve(
        request.request_id,
        approver="human_operator",
        comments="Approved after review",
    )
    print(f"\n✅ Approved by human operator")
    
    # Show statistics
    stats = promotion.get_statistics()
    print(f"\n📈 Promotion Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Pending Approvals: {stats['pending_approvals']}")
    print(f"   Production Items: {stats['production_items']}")


async def demo_market_opportunity_discovery():
    """Demo 6: Market Opportunity Discovery"""
    print("\n" + "=" * 70)
    print("DEMO 6: MARKET OPPORTUNITY DISCOVERY")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import MarketOpportunityDiscovery
    
    discovery = MarketOpportunityDiscovery()
    
    print("\n✅ Market Opportunity Discovery initialized")
    
    # Start discovery
    await discovery.start()
    print("\n▶️ Discovery engine started")
    
    # Wait for some discoveries
    print("\n🔍 Scanning markets for opportunities...")
    await asyncio.sleep(3)
    
    # Get top opportunities
    opportunities = discovery.get_top_opportunities(limit=5)
    
    print(f"\n📊 Top Opportunities Found: {len(opportunities)}")
    for opp in opportunities:
        print(f"\n   🎯 {opp.opportunity_id}")
        print(f"      Type: {opp.opportunity_type.value}")
        print(f"      Symbols: {', '.join(opp.symbols)}")
        print(f"      Direction: {opp.direction}")
        print(f"      Score: {opp.score:.1f}")
        print(f"      Confidence: {opp.confidence:.1%}")
        print(f"      Expected Return: {opp.expected_return:.1%}")
    
    # Stop discovery
    await discovery.stop()
    
    # Show statistics
    stats = discovery.get_statistics()
    print(f"\n📈 Discovery Statistics:")
    print(f"   Total Scans: {stats['total_scans']}")
    print(f"   Signals Detected: {stats['signals_detected']}")
    print(f"   Opportunities Created: {stats['opportunities_created']}")


async def demo_self_programming_proposer():
    """Demo 7: Self-Programming Proposer"""
    print("\n" + "=" * 70)
    print("DEMO 7: SELF-PROGRAMMING PROPOSER")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import SelfProgrammingProposer
    
    proposer = SelfProgrammingProposer(storage_path="demo_improvements")
    
    print("\n✅ Self-Programming Proposer initialized")
    
    # Start proposer
    await proposer.start()
    print("\n▶️ Self-programming engine started")
    
    # Wait for proposals
    print("\n🧠 Analyzing performance and generating improvements...")
    await asyncio.sleep(3)
    
    # Get pending improvements
    improvements = proposer.get_pending_improvements()
    
    print(f"\n📊 Improvements Proposed: {len(improvements)}")
    for imp in improvements[:3]:
        print(f"\n   💡 {imp.improvement_id}")
        print(f"      Title: {imp.title}")
        print(f"      Type: {imp.improvement_type.value}")
        print(f"      Priority: {imp.priority.name}")
        print(f"      Status: {imp.status.name}")
        print(f"      Estimated Improvement: {imp.estimated_improvement:.1%}")
        print(f"      Confidence: {imp.confidence:.1%}")
    
    # Stop proposer
    await proposer.stop()
    
    # Show statistics
    stats = proposer.get_statistics()
    print(f"\n📈 Self-Programming Statistics:")
    print(f"   Total Analyses: {stats['total_analyses']}")
    print(f"   Total Proposals: {stats['total_proposals']}")
    print(f"   Code Generated: {stats['code_generated']}")


async def demo_full_orchestrator():
    """Demo 8: Full Self-Coordinating AI Orchestrator"""
    print("\n" + "=" * 70)
    print("DEMO 8: FULL SELF-COORDINATING AI ORCHESTRATOR")
    print("=" * 70)
    
    from trading_bot.self_coordinating_ai import (
        SelfCoordinatingAIOrchestrator, OrchestratorConfig
    )
    
    config = OrchestratorConfig(
        enable_discovery=True,
        enable_self_programming=True,
        enable_auto_experimentation=True,
        enable_auto_promotion=False,  # Require human approval
        max_concurrent_experiments=3,
    )
    
    orchestrator = SelfCoordinatingAIOrchestrator(config)
    
    print("\n🚀 Initializing Self-Coordinating AI Infrastructure...")
    await orchestrator.initialize()
    
    print("\n▶️ Starting orchestrator...")
    await orchestrator.start()
    
    # Let it run for a bit
    print("\n⏳ Running autonomous operations...")
    await asyncio.sleep(5)
    
    # Get status
    status = orchestrator.get_status()
    
    print(f"\n" + "=" * 70)
    print("ORCHESTRATOR STATUS")
    print("=" * 70)
    
    print(f"\n📊 System State: {status.state.name}")
    print(f"   Uptime: {status.uptime_seconds:.1f}s")
    print(f"   Overall Health: {status.overall_health:.1%}")
    
    print(f"\n🔧 Components:")
    print(f"   Production System: {'✓' if status.production_system_active else '✗'}")
    print(f"   Discovery Engine: {'✓' if status.discovery_engine_active else '✗'}")
    print(f"   Self-Programming: {'✓' if status.self_programming_active else '✗'}")
    
    print(f"\n📈 Activity:")
    print(f"   Active Experiments: {status.active_experiments}")
    print(f"   Pending Promotions: {status.pending_promotions}")
    print(f"   Active Opportunities: {status.active_opportunities}")
    print(f"   Pending Improvements: {status.pending_improvements}")
    
    print(f"\n🏥 Component Health:")
    for component, health in status.component_health.items():
        icon = '✓' if health > 0.9 else ('⚠' if health > 0.5 else '✗')
        print(f"   {icon} {component}: {health:.0%}")
    
    # Get comprehensive statistics
    stats = orchestrator.get_statistics()
    
    print(f"\n📊 Comprehensive Statistics:")
    print(f"   Total Experiments: {stats['orchestrator']['total_experiments']}")
    print(f"   Successful Experiments: {stats['orchestrator']['successful_experiments']}")
    print(f"   Total Promotions: {stats['orchestrator']['total_promotions']}")
    print(f"   Opportunities Discovered: {stats['orchestrator']['opportunities_discovered']}")
    print(f"   Improvements Proposed: {stats['orchestrator']['improvements_proposed']}")
    print(f"   Safety Blocks: {stats['orchestrator']['safety_blocks']}")
    
    # Stop orchestrator
    print("\n⏹️ Stopping orchestrator...")
    await orchestrator.stop()
    
    print("\n✅ Orchestrator stopped successfully")


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("AUTONOMOUS FINANCIAL INTELLIGENCE INFRASTRUCTURE")
    print("COMPREHENSIVE DEMONSTRATION")
    print("=" * 70)
    
    print("\n🏗️ Architecture Overview:")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │                 SELF-COORDINATING AI ORCHESTRATOR               │
    ├─────────────────────────────────────────────────────────────────┤
    │  ┌────────────────┐    ┌────────────────┐    ┌──────────────┐  │
    │  │   DISCOVERY    │───▶│ SELF-PROGRAMMING│───▶│  EXPERIMENT  │  │
    │  │    ENGINE      │    │    PROPOSER     │    │   REGISTRY   │  │
    │  └────────────────┘    └────────────────┘    └──────────────┘  │
    │           │                    │                    │           │
    │           ▼                    ▼                    ▼           │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │                    SAFETY LAYER                            ││
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   ││
    │  │  │  CODE    │  │  DATA    │  │ COMPUTE  │  │  SANDBOX │   ││
    │  │  │ SCANNER  │  │ FIREWALL │  │  BUDGET  │  │ EXECUTOR │   ││
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   ││
    │  └────────────────────────────────────────────────────────────┘│
    │                              │                                  │
    │                              ▼                                  │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │                   PROMOTION SYSTEM                         ││
    │  │  Safety Review ─▶ Performance Review ─▶ Approval ─▶ Stage  ││
    │  └────────────────────────────────────────────────────────────┘│
    │                              │                                  │
    │                              ▼                                  │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │              CORE PRODUCTION SYSTEM (IMMUTABLE)            ││
    │  └────────────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────────────┘
    """)
    
    print("\n🔑 Key Features:")
    print("  1. Core Production System - IMMUTABLE, cannot be modified by AI")
    print("  2. Sandbox Environment - All AI code runs in isolation first")
    print("  3. Compute Budget Controller - Resource limits and allocation")
    print("  4. Experiment Registry - Track all experiments and results")
    print("  5. Data Integrity Firewall - Protect production data")
    print("  6. Code Safety Scanner - Block dangerous code patterns")
    print("  7. Promotion System - Multi-stage approval for production")
    print("  8. Market Opportunity Discovery - Autonomous market scanning")
    print("  9. Self-Programming Proposer - AI proposes improvements")
    
    try:
        await demo_core_production_system()
        await demo_sandbox_executor()
        await demo_code_safety_scanner()
        await demo_experiment_registry()
        await demo_promotion_system()
        await demo_market_opportunity_discovery()
        await demo_self_programming_proposer()
        await demo_full_orchestrator()
        
        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        print("\n🎉 The Autonomous Financial Intelligence Infrastructure is ready!")
        print("   - AI discovers market opportunities autonomously")
        print("   - AI proposes improvements continuously")
        print("   - All changes run in sandbox first")
        print("   - Production system remains immutable")
        print("   - Human approval required for promotions")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
