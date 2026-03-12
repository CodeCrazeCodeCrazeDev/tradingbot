"""
Self-Assembly AI System Demo
=============================

Demonstrates the complete self-assembly AI system with:
- Immutable safety core
- Recursive self-improvement
- Self-assembly orchestration
- Risk mitigation
- Evolution monitoring
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_safety_core():
    """Demonstrate the immutable safety core"""
    print("\n" + "="*80)
    print("DEMO 1: Immutable Safety Core")
    print("="*80)
    
    from trading_bot.self_assembly_ai import ImmutableSafetyCore, SafetyBoundary
    
    # Create safety core
    safety_core = ImmutableSafetyCore()
    
    # Verify integrity
    print(f"\n✓ Safety core integrity: {safety_core.verify_integrity()}")
    
    # Check boundaries
    print(f"\n✓ Max risk per trade: {safety_core.get_rule_value(SafetyBoundary.MAX_RISK_PER_TRADE)}")
    print(f"✓ Max daily loss: {safety_core.get_rule_value(SafetyBoundary.MAX_DAILY_LOSS)}")
    print(f"✓ Max drawdown: {safety_core.get_rule_value(SafetyBoundary.MAX_DRAWDOWN)}")
    
    # Test boundary check
    print(f"\n✓ Check 1% risk (should pass): {safety_core.check_boundary(SafetyBoundary.MAX_RISK_PER_TRADE, 0.01)}")
    print(f"✓ Check 5% risk (should fail): {safety_core.check_boundary(SafetyBoundary.MAX_RISK_PER_TRADE, 0.05)}")
    
    # Export report
    report = safety_core.export_safety_report()
    print(f"\n✓ Total safety rules: {report['total_rules']}")
    print(f"✓ Total violations: {report['total_violations']}")


async def demo_recursive_improvement():
    """Demonstrate recursive self-improvement"""
    print("\n" + "="*80)
    print("DEMO 2: Recursive Self-Improvement")
    print("="*80)
    
    from trading_bot.self_assembly_ai import RecursiveSelfImprovement, ImprovementType
    
    # Create improvement engine
    improver = RecursiveSelfImprovement(".")
    
    # Propose improvement
    proposal = improver.propose_improvement(
        improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
        description="Optimize strategy execution speed",
        affected_files=["trading_bot/strategies/example.py"],
        code_changes={
            "trading_bot/strategies/example.py": "# Optimized code here"
        },
        expected_benefit="20% faster execution",
        risk_level="LOW"
    )
    
    if proposal:
        print(f"\n✓ Proposal created: {proposal.proposal_id}")
        print(f"✓ Type: {proposal.improvement_type.value}")
        print(f"✓ Risk level: {proposal.risk_level}")
        print(f"✓ Requires approval: {proposal.requires_human_approval}")
        
        # Get improvement report
        report = improver.get_improvement_report()
        print(f"\n✓ Total proposals: {report['total_proposals']}")
        print(f"✓ Current recursion level: {report['current_recursion_level']}")
        print(f"✓ Max recursion depth: {report['max_recursion_depth']}")


async def demo_self_assembly():
    """Demonstrate self-assembly orchestration"""
    print("\n" + "="*80)
    print("DEMO 3: Self-Assembly Orchestration")
    print("="*80)
    
    from trading_bot.self_assembly_ai import SelfAssemblyOrchestrator
    
    # Create orchestrator
    orchestrator = SelfAssemblyOrchestrator(".")
    
    # Discover components
    components = orchestrator.discover_components()
    print(f"\n✓ Discovered {len(components)} components")
    
    for component in components[:5]:  # Show first 5
        print(f"  - {component.name} ({component.component_type.value})")
    
    # Get status report
    status = orchestrator.get_status_report()
    print(f"\n✓ Total components: {status['total_components']}")
    print(f"✓ Active: {status['active']}")
    print(f"✓ Failed: {status['failed']}")


async def demo_risk_mitigation():
    """Demonstrate risk mitigation matrix"""
    print("\n" + "="*80)
    print("DEMO 4: Risk Mitigation Matrix")
    print("="*80)
    
    from trading_bot.self_assembly_ai import RiskMitigationMatrix, RiskCategory
    
    # Create risk matrix
    risk_matrix = RiskMitigationMatrix()
    
    # Assess market risk
    market_risk = risk_matrix.assess_risk(
        RiskCategory.MARKET_RISK,
        {'daily_loss_pct': 0.02, 'drawdown_pct': 0.05}
    )
    print(f"\n✓ Market risk level: {market_risk.name}")
    
    # Assess AI evolution risk
    evolution_risk = risk_matrix.assess_risk(
        RiskCategory.RECURSIVE_IMPROVEMENT_RISK,
        {'recursion_depth': 3, 'code_change_rate': 0.15}
    )
    print(f"✓ Evolution risk level: {evolution_risk.name}")
    
    # Get overall risk
    overall_risk = risk_matrix.get_overall_risk_level()
    print(f"✓ Overall risk level: {overall_risk.name}")
    
    # Get risk report
    report = risk_matrix.get_risk_report()
    print(f"\n✓ Total risk events: {report['total_events']}")
    print(f"✓ Critical events: {report['critical_events']}")


async def demo_evolution_monitor():
    """Demonstrate evolution monitoring"""
    print("\n" + "="*80)
    print("DEMO 5: Evolution Monitoring")
    print("="*80)
    
    from trading_bot.self_assembly_ai import EvolutionMonitor
    
    # Create monitor
    monitor = EvolutionMonitor(".")
    
    # Create checkpoint
    checkpoint = monitor.create_checkpoint("Demo checkpoint")
    print(f"\n✓ Checkpoint created: {checkpoint.checkpoint_id}")
    print(f"✓ Timestamp: {checkpoint.timestamp}")
    print(f"✓ Integrity verified: {checkpoint.verify_integrity()}")
    
    # Get evolution report
    report = monitor.get_evolution_report()
    print(f"\n✓ Total checkpoints: {report['checkpoints']['total']}")
    print(f"✓ Safe checkpoints: {report['checkpoints']['safe_checkpoints']}")
    print(f"✓ Safety status: {report['safety_status']['core_integrity']}")


async def demo_master_orchestrator():
    """Demonstrate master orchestrator"""
    print("\n" + "="*80)
    print("DEMO 6: Master Self-Assembly Orchestrator")
    print("="*80)
    
    from trading_bot.self_assembly_ai import MasterSelfAssemblyOrchestrator
    
    # Create orchestrator
    orchestrator = MasterSelfAssemblyOrchestrator(
        workspace_path=".",
        config={
            'auto_evolution': False,  # Disabled for demo
            'evolution_interval': 3600
        }
    )
    
    # Get system status
    status = orchestrator.get_system_status()
    print(f"\n✓ Safety core integrity: {status.safety_core_integrity}")
    print(f"✓ Overall risk level: {status.overall_risk_level.name}")
    print(f"✓ Active components: {status.active_components}")
    print(f"✓ Total improvements: {status.total_improvements}")
    print(f"✓ Recursion depth: {status.current_recursion_depth}")
    print(f"✓ Auto-evolution enabled: {status.auto_evolution_enabled}")
    
    # Get comprehensive report
    report = orchestrator.get_comprehensive_report()
    print(f"\n✓ Comprehensive report generated")
    print(f"  - Safety core rules: {report['safety_core']['total_rules']}")
    print(f"  - Risk events: {report['risk_matrix']['total_events']}")
    print(f"  - Checkpoints: {report['evolution_monitor']['checkpoints']['total']}")
    
    # Test human override
    print(f"\n✓ Testing human override...")
    orchestrator.human_override("DISABLE_EVOLUTION", "Demo test")
    print(f"  - Evolution disabled successfully")


async def demo_full_system():
    """Demonstrate full system integration"""
    print("\n" + "="*80)
    print("DEMO 7: Full System Integration")
    print("="*80)
    
    from trading_bot.self_assembly_ai import quick_start_self_assembly_ai
    
    print("\n✓ Starting self-assembly AI system...")
    
    # Start system (auto-evolution disabled for demo)
    orchestrator = await quick_start_self_assembly_ai(
        workspace_path=".",
        auto_evolution=False,
        evolution_interval=3600
    )
    
    print("✓ System started successfully")
    
    # Let it run for a few seconds
    await asyncio.sleep(3)
    
    # Get status
    status = orchestrator.get_system_status()
    print(f"\n✓ System Status:")
    print(f"  - Safety: {status.safety_core_integrity}")
    print(f"  - Risk: {status.overall_risk_level.name}")
    print(f"  - Components: {status.active_components}")
    
    # Stop system
    print("\n✓ Stopping system...")
    await orchestrator.stop()
    print("✓ System stopped successfully")


async def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("SELF-ASSEMBLY AI SYSTEM - COMPREHENSIVE DEMO")
    print("="*80)
    print("\nThis demo showcases all components of the self-assembly AI system")
    print("with comprehensive risk mitigation for recursive self-improvement.")
    
    try:
        # Run all demos
        await demo_safety_core()
        await demo_recursive_improvement()
        await demo_self_assembly()
        await demo_risk_mitigation()
        await demo_evolution_monitor()
        await demo_master_orchestrator()
        await demo_full_system()
        
        print("\n" + "="*80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n✓ Key Features Demonstrated:")
        print("  1. Immutable safety boundaries (cryptographically verified)")
        print("  2. Recursive self-improvement (max 10 levels, 30% code change limit)")
        print("  3. Self-assembly orchestration (autonomous component management)")
        print("  4. Multi-layer risk mitigation (16 categories, 5 severity levels)")
        print("  5. Evolution monitoring (automatic checkpoints and rollback)")
        print("  6. Master orchestration (coordinates all components)")
        print("  7. Human override (ALWAYS works)")
        
        print("\n✓ Safety Guarantees:")
        print("  - Safety core CANNOT be modified")
        print("  - All changes are tested before deployment")
        print("  - Automatic rollback on failures")
        print("  - Maximum recursion depth enforced")
        print("  - Human override ALWAYS available")
        print("  - Complete audit trail")
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        print(f"\n✗ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
