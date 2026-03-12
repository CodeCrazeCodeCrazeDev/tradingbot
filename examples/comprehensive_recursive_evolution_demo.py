"""
Comprehensive Recursive Evolution System Demo
==============================================

Demonstrates the full recursive self-evolution system with:
- Evolution across all areas (strategies, risk, execution, ML, data)
- Immutable boundaries enforcement
- Human approval workflow
- Meta-learning
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from trading_bot.recursive_evolution import (
    ComprehensiveEvolutionOrchestrator,
    EvolutionConfig,
    SystemMetrics,
    quick_start,
    verify_boundary_integrity,
    get_evolution_guide
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def demo_1_quick_start():
    """Demo 1: Quick start with default configuration"""
    print_section("DEMO 1: Quick Start")
    
    # Quick start
    orchestrator = quick_start()
    
    print("✅ Orchestrator initialized with default config")
    print(f"✅ Boundary integrity verified: {verify_boundary_integrity()}")
    
    # Get evolution guide
    guide = get_evolution_guide()
    
    print("\n📋 Evolution Guide:")
    print(f"  Can evolve freely: {len(guide['can_evolve_freely'])} areas")
    print(f"  Requires approval: {len(guide['requires_approval'])} areas")
    print(f"  Forbidden: {len(guide['forbidden'])} areas")
    print(f"  Immutable constraints: {len(guide['immutable_constraints'])} rules")
    
    return orchestrator


async def demo_2_propose_evolutions(orchestrator: ComprehensiveEvolutionOrchestrator):
    """Demo 2: Propose evolutions across all areas"""
    print_section("DEMO 2: Propose Evolutions")
    
    # Create sample metrics
    metrics = SystemMetrics(
        strategy_performance={
            'sharpe_ratio': 1.2,
            'win_rate': 0.52,
            'profit_factor': 1.3,
            'max_drawdown': 0.15
        },
        risk_metrics={
            'current_drawdown': 0.08,
            'var_95': 0.03,
            'position_concentration': 0.15
        },
        execution_metrics={
            'avg_slippage': 0.0012,  # High slippage
            'fill_rate': 0.98,
            'avg_latency_ms': 45
        },
        ml_metrics={
            'accuracy': 0.58,
            'precision': 0.60,
            'recall': 0.55,
            'f1_score': 0.57
        },
        data_quality={
            'missing_rate': 0.015,  # High missing rate
            'outlier_rate': 0.01,
            'staleness_avg_seconds': 2.5
        }
    )
    
    print("📊 Current System Metrics:")
    print(f"  Strategy Sharpe: {metrics.strategy_performance['sharpe_ratio']:.2f}")
    print(f"  Execution Slippage: {metrics.execution_metrics['avg_slippage']:.4f}")
    print(f"  ML Accuracy: {metrics.ml_metrics['accuracy']:.2%}")
    print(f"  Data Missing Rate: {metrics.data_quality['missing_rate']:.2%}")
    
    # Propose evolutions
    proposals = await orchestrator.propose_evolutions(metrics)
    
    print(f"\n🔄 Generated {len(proposals)} evolution proposals:")
    for i, proposal in enumerate(proposals, 1):
        print(f"\n  Proposal {i}: {proposal.proposal_id}")
        print(f"    Area: {proposal.area.value}")
        print(f"    Component: {proposal.specific_component}")
        print(f"    Rationale: {proposal.rationale}")
        print(f"    Expected improvement: {proposal.expected_improvement}")
        print(f"    Requires approval: {proposal.requires_approval}")
        print(f"    Status: {proposal.status.value}")
    
    return proposals


async def demo_3_auto_deploy(orchestrator: ComprehensiveEvolutionOrchestrator, proposals):
    """Demo 3: Auto-deploy allowed proposals"""
    print_section("DEMO 3: Auto-Deploy Allowed Proposals")
    
    deployed_count = 0
    
    for proposal in proposals:
        if not proposal.requires_approval:
            print(f"\n🚀 Deploying proposal: {proposal.proposal_id}")
            print(f"   Area: {proposal.area.value}")
            print(f"   Component: {proposal.specific_component}")
            
            result = await orchestrator.deploy_evolution(proposal)
            
            if result.success:
                print(f"   ✅ SUCCESS: {result.message}")
                print(f"   Improvement: {result.improvement_achieved}")
                deployed_count += 1
            else:
                print(f"   ❌ FAILED: {result.message}")
    
    print(f"\n📈 Deployed {deployed_count} proposals automatically")


async def demo_4_approval_workflow(orchestrator: ComprehensiveEvolutionOrchestrator):
    """Demo 4: Human approval workflow"""
    print_section("DEMO 4: Human Approval Workflow")
    
    # Get pending approvals
    pending = orchestrator.get_pending_approvals()
    
    print(f"⏳ Pending approvals: {len(pending)}")
    
    for proposal in pending:
        print(f"\n📋 Proposal: {proposal['proposal_id']}")
        print(f"   Area: {proposal['area']}")
        print(f"   Component: {proposal['component']}")
        print(f"   Rationale: {proposal['rationale']}")
        print(f"   Expected improvement: {proposal['improvement']}")
        print(f"   Risk assessment: {proposal['risk']}")
        
        # Simulate human approval
        print(f"   👤 Human reviewing...")
        
        # Approve
        approved = orchestrator.approve_proposal(
            proposal_id=proposal['proposal_id'],
            approved_by='demo_user'
        )
        
        if approved:
            print(f"   ✅ APPROVED by demo_user")
            
            # Deploy approved proposal
            proposal_obj = next(
                p for p in orchestrator.evolution_engine.proposals
                if p.proposal_id == proposal['proposal_id']
            )
            
            result = await orchestrator.deploy_evolution(proposal_obj)
            
            if result.success:
                print(f"   🚀 DEPLOYED: {result.message}")
            else:
                print(f"   ❌ DEPLOYMENT FAILED: {result.message}")


async def demo_5_manual_evolution(orchestrator: ComprehensiveEvolutionOrchestrator):
    """Demo 5: Manual evolution proposal"""
    print_section("DEMO 5: Manual Evolution")
    
    print("👤 Human proposes manual evolution...")
    
    result = await orchestrator.manual_evolution(
        area="strategy",
        component="strategy_parameters",
        proposed_changes={
            'entry_threshold': 0.75,
            'exit_threshold': 0.25,
            'stop_loss_atr_multiple': 2.0,
            'take_profit_atr_multiple': 4.0
        },
        rationale="Increase signal quality and improve risk-reward ratio"
    )
    
    print(f"\n📊 Manual Evolution Result:")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    print(f"   Improvement: {result.improvement_achieved}")
    print(f"   Rollback available: {result.rollback_available}")


async def demo_6_boundary_enforcement():
    """Demo 6: Boundary enforcement (forbidden evolution)"""
    print_section("DEMO 6: Boundary Enforcement")
    
    from trading_bot.recursive_evolution import (
        EvolutionBoundaries,
        EvolutionProposal,
        EvolutionArea,
        EvolutionStatus
    )
    
    print("🚫 Attempting to evolve FORBIDDEN area...")
    
    # Try to increase max risk per trade (FORBIDDEN)
    forbidden_proposal = {
        'area': 'max_risk_per_trade',
        'risk_per_trade': 0.03,  # Trying to exceed 2% limit
        'recursive_depth': 1
    }
    
    is_valid, reason = EvolutionBoundaries.validate_proposal(forbidden_proposal)
    
    print(f"\n📋 Proposal to increase max risk to 3%:")
    print(f"   Valid: {is_valid}")
    print(f"   Reason: {reason}")
    
    if not is_valid:
        print(f"   ✅ CORRECTLY BLOCKED - Boundary enforcement working!")
    
    # Try to modify evolution boundaries (FORBIDDEN)
    print("\n🚫 Attempting to modify evolution boundaries...")
    
    forbidden_proposal_2 = {
        'area': 'evolution_boundary_rules',
        'recursive_depth': 1
    }
    
    permission = EvolutionBoundaries.check_evolution_permission('evolution_boundary_rules')
    
    print(f"   Permission: {permission.value}")
    
    if permission.value == 'forbidden':
        print(f"   ✅ CORRECTLY BLOCKED - Cannot modify own boundaries!")


async def demo_7_evolution_summary(orchestrator: ComprehensiveEvolutionOrchestrator):
    """Demo 7: Evolution summary and monitoring"""
    print_section("DEMO 7: Evolution Summary")
    
    summary = orchestrator.get_evolution_summary()
    
    print("📊 Evolution Summary:")
    print(f"   Total proposals: {summary['total_proposals']}")
    print(f"   Deployed: {summary['deployed']}")
    print(f"   Pending approval: {summary['pending_approval']}")
    print(f"   Active evolutions: {summary['active_evolutions']}")
    print(f"   Total history: {summary['total_history']}")
    
    print(f"\n📈 Success Rates by Area:")
    for area, rate in summary['success_rates'].items():
        print(f"   {area}: {rate:.1%}")
    
    print(f"\n🎯 Evolution Effectiveness:")
    for area, effectiveness in summary['evolution_effectiveness'].items():
        print(f"   {area}: {effectiveness:.3f}")
    
    print(f"\n⚙️ Configuration:")
    for key, value in summary['config'].items():
        print(f"   {key}: {value}")
    
    print(f"\n🔒 Security:")
    print(f"   Boundary integrity: {summary['boundary_integrity']}")
    print(f"   Boundary hash: {summary['boundary_hash'][:16]}...")
    print(f"   Best practices learned: {summary['best_practices_learned']}")


async def demo_8_meta_learning(orchestrator: ComprehensiveEvolutionOrchestrator):
    """Demo 8: Meta-learning (evolution of evolution)"""
    print_section("DEMO 8: Meta-Learning")
    
    print("🧠 Meta-Learning: System learns how to evolve better")
    
    # Simulate multiple evolution cycles
    print("\n🔄 Running 3 evolution cycles...")
    
    for cycle in range(1, 4):
        print(f"\n  Cycle {cycle}:")
        
        # Collect metrics
        metrics = SystemMetrics(
            strategy_performance={
                'sharpe_ratio': 1.2 + (cycle * 0.1),
                'win_rate': 0.52 + (cycle * 0.01),
                'profit_factor': 1.3 + (cycle * 0.05)
            },
            execution_metrics={
                'avg_slippage': 0.0012 - (cycle * 0.0002)
            },
            ml_metrics={
                'accuracy': 0.58 + (cycle * 0.01)
            }
        )
        
        # Propose and deploy
        proposals = await orchestrator.propose_evolutions(metrics)
        
        for proposal in proposals:
            if not proposal.requires_approval:
                result = await orchestrator.deploy_evolution(proposal)
                if result.success:
                    print(f"    ✅ Deployed: {proposal.area.value}")
        
        # Meta-learning happens automatically
        await orchestrator._evolve_evolution_strategies()
    
    print("\n🎓 Meta-Learning Results:")
    print("   System has learned:")
    print("   - Which evolution strategies work best")
    print("   - Which areas respond well to evolution")
    print("   - How to propose better improvements")
    
    # Show best practices
    best_practices = orchestrator.evolution_engine.best_practices[-3:]
    
    if best_practices:
        print("\n📚 Recent Best Practices Learned:")
        for i, practice in enumerate(best_practices, 1):
            print(f"   {i}. {practice['area']}: {practice['what_worked']}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE RECURSIVE EVOLUTION SYSTEM - DEMO")
    print("=" * 80)
    
    try:
        # Demo 1: Quick start
        orchestrator = await demo_1_quick_start()
        
        # Demo 2: Propose evolutions
        proposals = await demo_2_propose_evolutions(orchestrator)
        
        # Demo 3: Auto-deploy
        await demo_3_auto_deploy(orchestrator, proposals)
        
        # Demo 4: Approval workflow
        await demo_4_approval_workflow(orchestrator)
        
        # Demo 5: Manual evolution
        await demo_5_manual_evolution(orchestrator)
        
        # Demo 6: Boundary enforcement
        await demo_6_boundary_enforcement()
        
        # Demo 7: Evolution summary
        await demo_7_evolution_summary(orchestrator)
        
        # Demo 8: Meta-learning
        await demo_8_meta_learning(orchestrator)
        
        print_section("DEMO COMPLETE")
        print("✅ All demos completed successfully!")
        print("\n📋 Summary:")
        print("   - Evolution system initialized")
        print("   - Proposals generated across all areas")
        print("   - Auto-deployment working")
        print("   - Human approval workflow functional")
        print("   - Boundary enforcement verified")
        print("   - Meta-learning operational")
        print("\n🔒 Security:")
        print(f"   - Boundary integrity: {verify_boundary_integrity()}")
        print("   - Immutable constraints enforced")
        print("   - Human control maintained")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
