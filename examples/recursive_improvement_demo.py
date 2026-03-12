"""
Recursive Self-Improvement System Demo

Demonstrates the complete recursive self-improvement system.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demo_recursive_improvement():
    """Demonstrate recursive self-improvement system"""
    
    print("\n" + "="*80)
    print("RECURSIVE SELF-IMPROVEMENT SYSTEM DEMO")
    print("="*80 + "\n")
    
    try:
        from trading_bot.recursive_improvement import (
            RecursiveImprovementOrchestrator,
            quick_start,
            create_recursive_system
        )
        
        # Quick start
        print("1. Quick Start Demo")
        print("-" * 80)
        orchestrator = quick_start({
            'max_recursion_depth': 3,
            'improvement_interval': 60
        })
        print(f"✓ Orchestrator created")
        
        # Run single improvement cycle
        print("\n2. Running Improvement Cycle")
        print("-" * 80)
        cycle_result = await orchestrator.run_improvement_cycle()
        print(f"✓ Cycle completed in {cycle_result['duration']:.2f}s")
        print(f"  - Learning: {cycle_result['results'].get('learning', {}).get('summary', {})}")
        print(f"  - Strategy: {cycle_result['results'].get('strategy', {}).get('summary', {})}")
        print(f"  - Risk: {cycle_result['results'].get('risk', {}).get('summary', {})}")
        
        # Get comprehensive summary
        print("\n3. Comprehensive Summary")
        print("-" * 80)
        summary = orchestrator.get_comprehensive_summary()
        print(f"✓ Total cycles: {summary['total_cycles']}")
        print(f"✓ Core improvements: {summary['core']}")
        print(f"✓ Learning summary: {summary['learning']}")
        print(f"✓ Strategy summary: {summary['strategy']}")
        print(f"✓ Risk summary: {summary['risk']}")
        print(f"✓ Execution summary: {summary['execution']}")
        print(f"✓ Architecture summary: {summary['architecture']}")
        print(f"✓ Meta state: {summary['meta']}")
        
        # Demonstrate individual components
        print("\n4. Individual Component Demos")
        print("-" * 80)
        
        # Learning recursion
        print("\n4.1 Learning Recursion")
        data = {'sample': True, 'value': 42}
        learning_results = await orchestrator.learning.recursive_learn(data)
        print(f"✓ Learning completed: {len(learning_results)} layers processed")
        
        # Strategy evolution
        print("\n4.2 Strategy Evolution")
        evolution = await orchestrator.strategy.evolve_generation(0)
        print(f"✓ Generation evolved: {evolution}")
        
        # Risk optimization
        print("\n4.3 Risk Optimization")
        performance_data = {
            'sharpe_ratio': 1.5,
            'max_drawdown': 0.10
        }
        market_conditions = {
            'volatility': 0.02,
            'liquidity': 0.8
        }
        risk_opt = await orchestrator.risk.optimize_risk_parameters(
            performance_data,
            market_conditions
        )
        print(f"✓ Risk optimized: {risk_opt}")
        
        # Execution optimization
        print("\n4.4 Execution Optimization")
        order = {
            'symbol': 'BTCUSDT',
            'size': 1.0,
            'direction': 'buy',
            'urgency': 'medium'
        }
        exec_plan = await orchestrator.execution.optimize_execution(
            order,
            market_conditions
        )
        print(f"✓ Execution plan: {exec_plan}")
        
        # Architecture evolution
        print("\n4.5 Architecture Evolution")
        architecture = {
            'modules': {
                'data': {'complexity': 1.0, 'dependencies': []},
                'signals': {'complexity': 2.0, 'dependencies': ['data']},
            }
        }
        metrics = {
            'modules': {
                'data': {'performance': 0.8},
                'signals': {'performance': 0.6},
            }
        }
        arch_evolved = await orchestrator.architecture.evolve_architecture(
            architecture,
            metrics
        )
        print(f"✓ Architecture evolved")
        
        # Meta-recursion
        print("\n4.6 Meta-Recursion Control")
        meta_state = orchestrator.meta.get_recursion_state()
        print(f"✓ Meta state: {meta_state}")
        
        # Demonstrate convergence detection
        print("\n5. Convergence Detection")
        print("-" * 80)
        for i in range(5):
            orchestrator.meta.convergence_detector.add_improvement(0.001 * (5 - i))
        
        has_converged = orchestrator.meta.convergence_detector.has_converged()
        convergence_score = orchestrator.meta.convergence_detector.get_convergence_score()
        print(f"✓ Has converged: {has_converged}")
        print(f"✓ Convergence score: {convergence_score:.3f}")
        
        # Save state
        print("\n6. State Persistence")
        print("-" * 80)
        orchestrator.save_state()
        print(f"✓ State saved")
        
        # Final summary
        print("\n7. Final Summary")
        print("-" * 80)
        final_summary = orchestrator.get_comprehensive_summary()
        print(f"✓ System Status:")
        print(f"  - Total improvement cycles: {final_summary['total_cycles']}")
        print(f"  - Integration points: {final_summary['integration_points']}")
        print(f"  - Running: {final_summary['is_running']}")
        
        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")


async def demo_continuous_improvement():
    """Demonstrate continuous improvement loop"""
    
    print("\n" + "="*80)
    print("CONTINUOUS IMPROVEMENT DEMO")
    print("="*80 + "\n")
    
    try:
        from trading_bot.recursive_improvement import create_recursive_system
        
        # Create system with auto-start
        orchestrator = await create_recursive_system(
            config={
                'improvement_interval': 10,  # 10 seconds for demo
                'meta': {'max_depth': 5}
            },
            auto_start=True
        )
        
        print("✓ Continuous improvement started")
        print("  Running for 30 seconds...")
        
        # Let it run for 30 seconds
        await asyncio.sleep(30)
        
        # Stop
        await orchestrator.stop()
        
        print("\n✓ Continuous improvement stopped")
        
        # Show results
        summary = orchestrator.get_comprehensive_summary()
        print(f"\nResults after 30 seconds:")
        print(f"  - Total cycles: {summary['total_cycles']}")
        print(f"  - Meta insights: {summary['meta'].get('meta_meta_insights', 0)}")
        
    except Exception as e:
        logger.error(f"Continuous demo failed: {e}", exc_info=True)
        print(f"\n❌ Continuous demo failed: {e}")


async def main():
    """Main demo function"""
    
    # Run basic demo
    await demo_recursive_improvement()
    
    # Optionally run continuous demo
    print("\nWould you like to run continuous improvement demo? (30 seconds)")
    print("(Skipping for automated demo)")
    # await demo_continuous_improvement()


if __name__ == "__main__":
    asyncio.run(main())
