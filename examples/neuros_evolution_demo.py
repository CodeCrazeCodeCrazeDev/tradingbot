"""
NEUROS Evolution Demo

Demonstrates the autonomous financial intelligence infrastructure with:
- Autonomous research agents
- Self-rewiring network
- Autonomous organization
- Continuous evolution
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot.neuros_evolution import (
    NeurosEvolutionOrchestrator,
    quick_start,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_research_agents(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 1: Autonomous Research Agents"""
    print("\n" + "="*80)
    print("DEMO 1: Autonomous Research Agents")
    print("="*80)
    
    # Simulate market data
    market_data = {
        'symbol': 'BTCUSDT',
        'price': 45000.0,
        'volume': 1000000.0,
        'volatility': 0.02,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    print("\n📊 Running research cycle with market data...")
    results = await orchestrator.run_research_cycle(market_data)
    
    print(f"\n✅ Research Results:")
    print(f"   - Hypotheses Generated: {len(results.get('hypotheses', []))}")
    print(f"   - ML Models Developed: {len(results.get('models', []))}")
    print(f"   - Insights Discovered: {len(results.get('insights', []))}")
    
    # Show sample hypotheses
    if results.get('hypotheses'):
        print(f"\n🔬 Sample Hypothesis:")
        hyp = results['hypotheses'][0]
        print(f"   - ID: {hyp.id}")
        print(f"   - Description: {hyp.description}")
        print(f"   - Status: {hyp.status.value}")
        print(f"   - Confidence: {hyp.confidence:.2f}")
    
    # Show sample insights
    if results.get('insights'):
        print(f"\n💡 Sample Insight:")
        insight = results['insights'][0]
        print(f"   - Type: {insight.insight_type}")
        print(f"   - Description: {insight.description}")
        print(f"   - Novelty Score: {insight.novelty_score:.2f}")
        print(f"   - Actionability: {insight.actionability_score:.2f}")


async def demo_adaptive_network(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 2: Self-Rewiring Network"""
    print("\n" + "="*80)
    print("DEMO 2: Self-Rewiring Network Infrastructure")
    print("="*80)
    
    print("\n🌐 Processing data flows through adaptive network...")
    
    # Process multiple data flows
    flows = [
        ('data_ingestion', 'preprocessing', 10.0, 8),
        ('preprocessing', 'feature_engineering', 5.0, 7),
        ('feature_engineering', 'signal_generation', 3.0, 9),
        ('signal_generation', 'risk_analysis', 2.0, 10),
    ]
    
    for source, dest, size, priority in flows:
        success = await orchestrator.process_data_flow(source, dest, size, priority)
        status = "✅" if success else "❌"
        print(f"   {status} Flow: {source} → {dest} ({size}MB, priority={priority})")
    
    # Show network status
    network_status = orchestrator.routing_network.get_network_status()
    print(f"\n📈 Network Status:")
    print(f"   - Total Nodes: {network_status['total_nodes']}")
    print(f"   - Total Edges: {network_status['total_edges']}")
    print(f"   - Active Flows: {network_status['active_flows']}")
    print(f"   - Avg Node Utilization: {network_status['avg_node_utilization']:.2%}")
    
    # Demonstrate load balancing
    print(f"\n⚖️ Running load balancing...")
    rebalance_result = await orchestrator.load_balancer.rebalance_load()
    print(f"   - Actions Taken: {rebalance_result['actions_taken']}")
    print(f"   - Overloaded Nodes: {rebalance_result['overloaded_nodes']}")
    print(f"   - Underloaded Nodes: {rebalance_result['underloaded_nodes']}")


async def demo_autonomous_organization(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 3: Autonomous Organization Management"""
    print("\n" + "="*80)
    print("DEMO 3: Autonomous Organization Management")
    print("="*80)
    
    # Create research projects
    print("\n📋 Creating research projects...")
    
    projects = [
        ("Momentum Strategy Research", "Develop advanced momentum indicators", 9, 30),
        ("ML Model Optimization", "Optimize neural network architectures", 8, 45),
        ("Risk Model Enhancement", "Improve VaR calculation methods", 10, 20),
    ]
    
    project_ids = []
    for name, desc, priority, duration in projects:
        project_id = orchestrator.create_research_project(name, desc, priority, duration)
        project_ids.append(project_id)
        print(f"   ✅ Created: {name} (Priority: {priority})")
    
    # Show project status
    print(f"\n📊 Project Status:")
    for project_id in project_ids:
        status = orchestrator.project_manager.get_project_status(project_id)
        if status:
            print(f"   - {status['name']}")
            print(f"     Status: {status['status']}")
            print(f"     Progress: {status['progress']:.0%}")
            print(f"     Priority: {status['priority']}")
    
    # Show capital allocation
    print(f"\n💰 Capital Allocation:")
    
    # Allocate capital to strategies
    strategies = [
        ("momentum_strategy", 200000, 0.15, 0.08),
        ("mean_reversion", 150000, 0.12, 0.06),
        ("arbitrage", 100000, 0.08, 0.04),
    ]
    
    for strategy_id, amount, expected_return, risk in strategies:
        success = orchestrator.resource_economist.allocate_capital(
            strategy_id, amount, expected_return, risk
        )
        status = "✅" if success else "❌"
        print(f"   {status} {strategy_id}: ${amount:,.0f} (Return: {expected_return:.1%}, Risk: {risk:.1%})")
    
    allocation_summary = orchestrator.resource_economist.get_allocation_summary()
    print(f"\n   Total Allocated: ${allocation_summary['total_allocated']:,.0f}")
    print(f"   Available: ${allocation_summary['available']:,.0f}")
    print(f"   Utilization: {allocation_summary['utilization']:.1%}")


async def demo_evolution_engine(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 4: Continuous Evolution Engine"""
    print("\n" + "="*80)
    print("DEMO 4: Continuous Evolution Engine")
    print("="*80)
    
    # Propose architecture evolution
    print("\n🧬 Proposing architecture evolution...")
    proposal = await orchestrator.architecture_evolution.propose_evolution(
        'performance_optimization',
        'Add caching layer to reduce latency'
    )
    
    print(f"   - Proposal ID: {proposal.proposal_id}")
    print(f"   - Description: {proposal.description}")
    print(f"   - Expected Improvement: {proposal.expected_improvement:.1%}")
    print(f"   - Risk Score: {proposal.risk_score:.2f}")
    
    # Test evolution
    print(f"\n🧪 Testing evolution proposal...")
    test_results = await orchestrator.architecture_evolution.test_evolution(proposal)
    
    print(f"   - Performance Improvement: {test_results['performance_improvement']:.1%}")
    print(f"   - Stability Score: {test_results['stability_score']:.2f}")
    print(f"   - Compatibility Score: {test_results['compatibility_score']:.2f}")
    print(f"   - Status: {proposal.status.value}")
    
    # Deploy if validated
    if proposal.status.value == 'validated':
        print(f"\n🚀 Deploying validated evolution...")
        success = await orchestrator.architecture_evolution.deploy_evolution(proposal)
        print(f"   - Deployment: {'✅ Success' if success else '❌ Failed'}")
    
    # Show knowledge synthesis
    print(f"\n🧠 Knowledge Synthesis:")
    knowledge_summary = orchestrator.knowledge_synthesis.get_knowledge_summary()
    print(f"   - Total Knowledge Nodes: {knowledge_summary['total_nodes']}")
    print(f"   - Domains Covered: {len(knowledge_summary['domains'])}")
    print(f"   - Avg Confidence: {knowledge_summary['avg_confidence']:.2f}")
    
    # Show self-improvement
    print(f"\n📈 Self-Improvement Status:")
    improvement_summary = orchestrator.self_improvement.get_improvement_summary()
    
    print(f"   Current Metrics:")
    for metric, value in improvement_summary['current_metrics'].items():
        target = improvement_summary['target_metrics'][metric]
        progress = improvement_summary['progress'][metric]
        print(f"     - {metric}: {value:.2f} / {target:.2f} ({progress:.0%} complete)")


async def demo_background_evolution(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 5: Background Evolution Loops"""
    print("\n" + "="*80)
    print("DEMO 5: Background Evolution Loops")
    print("="*80)
    
    print("\n🔄 Starting background evolution loops...")
    await orchestrator.start()
    
    print(f"   - Evolution Loop: ✅ Running")
    print(f"   - Rebalancing Loop: ✅ Running")
    print(f"   - Improvement Loop: ✅ Running")
    print(f"   - Total Background Tasks: {len(orchestrator.background_tasks)}")
    
    # Let it run for a few seconds
    print(f"\n⏳ Running autonomous evolution for 5 seconds...")
    await asyncio.sleep(5)
    
    # Show updated status
    status = orchestrator.get_system_status()
    print(f"\n📊 System Status After Evolution:")
    print(f"   - Research Agents: {status['research']['total_agents']}")
    print(f"   - Active Projects: {status['organization']['active_projects']}")
    print(f"   - Architecture Version: {status['evolution']['architecture']['current_version']}")
    print(f"   - Knowledge Nodes: {status['evolution']['knowledge']['total_nodes']}")
    
    # Stop background tasks
    print(f"\n🛑 Stopping background evolution...")
    await orchestrator.stop()
    print(f"   - All background tasks stopped")


async def demo_performance_report(orchestrator: NeurosEvolutionOrchestrator):
    """Demo 6: Comprehensive Performance Report"""
    print("\n" + "="*80)
    print("DEMO 6: Comprehensive Performance Report")
    print("="*80)
    
    report = orchestrator.get_performance_report()
    
    print(f"\n📈 Research Productivity:")
    productivity = report['research_productivity']
    print(f"   - Hypotheses Generated: {productivity['hypotheses_generated']}")
    print(f"   - Hypotheses Validated: {productivity['hypotheses_validated']}")
    print(f"   - ML Models Tested: {productivity['models_tested']}")
    
    print(f"\n🌐 System Performance:")
    system_perf = report['system_performance']
    print(f"   - Network Nodes: {system_perf['network_efficiency']['total_nodes']}")
    print(f"   - Active Flows: {system_perf['network_efficiency']['active_flows']}")
    
    print(f"\n🏢 Organizational Intelligence:")
    org_intel = report['organizational_intelligence']
    print(f"   - Projects Completed: {org_intel['projects_completed']}")
    print(f"   - Capital Efficiency: {org_intel['capital_efficiency']:.1%}")
    
    print(f"\n🧬 Evolution Velocity:")
    evolution = report['evolution_velocity']
    print(f"   - Architecture Changes: {evolution['architecture_changes']}")
    print(f"   - Knowledge Nodes: {evolution['knowledge_nodes']}")
    print(f"   - Improvement Cycles: {evolution['improvement_cycles']}")


async def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("NEUROS EVOLUTION: Autonomous Financial Intelligence Infrastructure")
    print("="*80)
    print("\nBuilding on NEUROS-FI brain topology with:")
    print("  • Autonomous research agents")
    print("  • Self-rewiring network infrastructure")
    print("  • Autonomous organization management")
    print("  • Continuous evolution engine")
    
    # Create orchestrator
    print("\n🚀 Initializing NEUROS Evolution system...")
    orchestrator = quick_start({
        'initial_capital': 1000000.0,
        'num_quant_agents': 3,
        'num_ml_agents': 2,
        'num_microstructure_agents': 1,
        'num_discovery_agents': 2,
        'enable_auto_evolution': True,
        'enable_auto_rebalancing': True,
        'enable_self_improvement': True,
    })
    
    await orchestrator.initialize()
    print("✅ System initialized")
    
    try:
        # Run all demos
        await demo_research_agents(orchestrator)
        await demo_adaptive_network(orchestrator)
        await demo_autonomous_organization(orchestrator)
        await demo_evolution_engine(orchestrator)
        await demo_background_evolution(orchestrator)
        await demo_performance_report(orchestrator)
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n🎯 Key Achievements:")
        print("  ✅ Autonomous research agents discovering strategies")
        print("  ✅ Self-rewiring network optimizing data flow")
        print("  ✅ AI project managers coordinating initiatives")
        print("  ✅ Continuous evolution improving architecture")
        print("  ✅ Meta-learning optimizing learning strategies")
        print("  ✅ Self-improvement enhancing core capabilities")
        
        print("\n📊 Final System Status:")
        final_status = orchestrator.get_system_status()
        print(f"  - Total Research Agents: {final_status['research']['total_agents']}")
        print(f"  - Network Nodes: {final_status['network']['status']['total_nodes']}")
        print(f"  - Active Projects: {final_status['organization']['active_projects']}")
        print(f"  - Evolution Changes: {final_status['evolution']['architecture']['total_proposals']}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        if orchestrator.running:
            await orchestrator.stop()


if __name__ == '__main__':
    asyncio.run(main())
