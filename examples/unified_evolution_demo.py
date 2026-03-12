"""
Unified Evolution System Demo
==============================

Demonstrates recursive self-evolution integrated with all advanced systems:
- AAMIS v3, TAMIC, Adaptive Systems, Advanced Analysis, Advanced ML, Adversarial Decision
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.unified_evolution import (
    UnifiedEvolutionOrchestrator,
    quick_start_unified,
    EvolutionConfig,
    ModelType,
    SystemType,
    OptimizationMethod
)
import numpy as np


async def demo_unified_evolution():
    """Demonstrate unified evolution system"""
    
    print("=" * 80)
    print("UNIFIED EVOLUTION SYSTEM - INTEGRATED WITH ALL ADVANCED SYSTEMS")
    print("=" * 80)
    print()
    
    # Initialize orchestrator
    print("1. Initializing Unified Evolution Orchestrator...")
    config = EvolutionConfig(
        evolution_interval_seconds=3600,
        max_concurrent_evolutions=3,
        enable_cross_system_learning=True,
        enable_knowledge_transfer=True,
        default_optimization_method=OptimizationMethod.BAYESIAN
    )
    
    orchestrator = UnifiedEvolutionOrchestrator(config)
    print("✓ Unified orchestrator initialized")
    print()
    
    # Register systems
    print("2. Registering Advanced Systems...")
    print("-" * 80)
    
    # Register AAMIS v3
    orchestrator.register_aamis_v3(None)  # Placeholder
    print("✓ AAMIS v3 registered")
    
    # Register TAMIC
    orchestrator.register_tamic(None)
    print("✓ TAMIC registered")
    
    # Register Adaptive Systems
    orchestrator.register_adaptive_systems(None)
    print("✓ Adaptive Systems registered")
    
    # Register Advanced ML
    orchestrator.register_advanced_ml(None)
    print("✓ Advanced ML registered")
    
    # Register Adversarial Decision
    orchestrator.register_adversarial_decision(None)
    print("✓ Adversarial Decision registered")
    print()
    
    # Simulate model performance
    print("3. Recording Model Performance...")
    print("-" * 80)
    
    from trading_bot.unified_evolution.unified_model_evolver import ModelPerformance
    
    for model_type in [ModelType.AAMIS_INTELLIGENCE, ModelType.TAMIC_TIME_DECAY,
                       ModelType.ADAPTIVE_REGIME, ModelType.ML_ENSEMBLE]:
        perf = ModelPerformance(
            model_type=model_type,
            system_name=model_type.value.split('_')[0],
            accuracy=np.random.uniform(0.65, 0.85),
            precision=np.random.uniform(0.65, 0.85),
            recall=np.random.uniform(0.65, 0.85),
            f1_score=np.random.uniform(0.65, 0.85),
            sharpe_ratio=np.random.uniform(1.5, 2.5),
            win_rate=np.random.uniform(0.55, 0.70),
            profit_factor=np.random.uniform(1.3, 2.0),
            max_drawdown=np.random.uniform(0.10, 0.20),
            inference_time_ms=np.random.uniform(5, 20),
            memory_usage_mb=np.random.uniform(50, 200),
            adversarial_robustness=np.random.uniform(0.60, 0.80),
            out_of_sample_performance=np.random.uniform(0.60, 0.80),
            sample_size=1000
        )
        orchestrator.model_evolver.record_performance(perf)
        print(f"✓ {model_type.value}: Overall Score = {perf.overall_score():.3f}")
    
    print()
    
    # Run unified evolution cycle
    print("4. Running Unified Evolution Cycle...")
    print("-" * 80)
    
    results = await orchestrator.run_unified_cycle()
    
    print(f"Cycle #{results['cycle_number']} completed in {results['duration_seconds']:.2f}s")
    print()
    
    # Show phase results
    for phase_name, phase_results in results['phases'].items():
        print(f"Phase: {phase_name.replace('_', ' ').title()}")
        if isinstance(phase_results, dict):
            for key, value in phase_results.items():
                if not isinstance(value, (list, dict)):
                    print(f"  {key}: {value}")
        print()
    
    # Show unified status
    print("5. Unified Evolution Status...")
    print("-" * 80)
    
    status = orchestrator.get_unified_status()
    
    print(f"Running: {status['is_running']}")
    print(f"Evolution Cycles: {status['evolution_cycles']}")
    print(f"Systems Registered: {status['systems_registered']}")
    print(f"Models Tracked: {status['models_tracked']}")
    print()
    
    # Model Evolution Stats
    print("Model Evolution:")
    model_stats = status['model_evolution']
    print(f"  Total Proposals: {model_stats['total_proposals']}")
    print(f"  Successful: {model_stats['successful_evolutions']}")
    print(f"  Failed: {model_stats['failed_evolutions']}")
    print(f"  Success Rate: {model_stats['success_rate']:.1%}")
    print(f"  Average Improvement: {model_stats['average_improvement']:.3f}")
    print()
    
    # System Integration Stats
    print("System Integration:")
    integration_stats = status['system_integration']
    print(f"  Total Transfers: {integration_stats['total_transfers']}")
    print(f"  Successful: {integration_stats['successful_transfers']}")
    print(f"  Success Rate: {integration_stats['success_rate']:.1%}")
    print(f"  Average Improvement: {integration_stats['average_improvement']:.3f}")
    print(f"  Active Integrations: {integration_stats['active_integrations']}")
    print()
    
    # Optimization Stats
    print("Advanced Optimization:")
    opt_stats = status['optimization']
    print(f"  Total Optimizations: {opt_stats['total_optimizations']}")
    if opt_stats['total_optimizations'] > 0:
        print(f"  Average Best Score: {opt_stats['average_best_score']:.3f}")
        print(f"  Overall Best Score: {opt_stats['overall_best_score']:.3f}")
    print()
    
    # Cross-system learning visualization
    print("6. Knowledge Transfer Graph...")
    print("-" * 80)
    print(orchestrator.system_integrator.visualize_knowledge_graph())
    print()
    
    # Export report
    print("7. Exporting Unified Evolution Report...")
    print("-" * 80)
    
    report_path = "unified_evolution_report.json"
    orchestrator.export_unified_report(report_path)
    print(f"✓ Report exported to: {report_path}")
    print()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("SYSTEMS INTEGRATED:")
    print("✓ AAMIS v3 - Advanced Autonomous Market Intelligence System")
    print("✓ TAMIC - Time-Aware Market Intelligence Core")
    print("✓ Adaptive Systems - Adaptive learning and optimization")
    print("✓ Advanced Analysis - Pattern recognition and analysis")
    print("✓ Advanced ML - Machine learning models")
    print("✓ Adversarial Decision - Adversarial training and robustness")
    print()
    print("CAPABILITIES:")
    print("✓ Recursive model evolution across all systems")
    print("✓ Cross-system knowledge transfer")
    print("✓ Advanced hyperparameter optimization")
    print("✓ Bayesian, Genetic, PSO, Hyperband, Evolutionary Strategy")
    print("✓ Unified performance tracking")
    print("✓ Automatic integration and deployment")
    print()


async def demo_model_evolution():
    """Demonstrate model evolution in detail"""
    
    print("\n" + "=" * 80)
    print("DETAILED MODEL EVOLUTION DEMONSTRATION")
    print("=" * 80)
    print()
    
    from trading_bot.unified_evolution import UnifiedModelEvolver, ModelPerformance, ModelType
    
    evolver = UnifiedModelEvolver()
    
    # Register and track models
    print("A. Model Registration and Performance Tracking")
    print("-" * 80)
    
    for model_type in [ModelType.ADAPTIVE_REGIME, ModelType.ML_ENSEMBLE, ModelType.AAMIS_INTELLIGENCE]:
        evolver.register_model(model_type, None, model_type.value.split('_')[0])
        
        # Record multiple performance measurements
        for i in range(5):
            perf = ModelPerformance(
                model_type=model_type,
                system_name=model_type.value.split('_')[0],
                accuracy=0.70 + i * 0.02,
                precision=0.68 + i * 0.02,
                recall=0.72 + i * 0.02,
                f1_score=0.70 + i * 0.02,
                sharpe_ratio=1.8 + i * 0.1,
                win_rate=0.60 + i * 0.02,
                profit_factor=1.5 + i * 0.1,
                max_drawdown=0.15 - i * 0.01,
                inference_time_ms=10.0,
                memory_usage_mb=100.0,
                adversarial_robustness=0.70 + i * 0.02,
                out_of_sample_performance=0.68 + i * 0.02,
                sample_size=1000
            )
            evolver.record_performance(perf)
        
        print(f"✓ {model_type.value}: {len(evolver.performance_history[model_type])} measurements")
    
    print()
    
    # Identify opportunities
    print("B. Evolution Opportunity Discovery")
    print("-" * 80)
    
    opportunities = evolver.identify_evolution_opportunities()
    print(f"Found {len(opportunities)} evolution opportunities:")
    for model_type, priority in opportunities[:3]:
        print(f"  {model_type.value}: Priority = {priority:.2f}")
    print()
    
    # Generate proposals
    print("C. Evolution Proposal Generation")
    print("-" * 80)
    
    if opportunities:
        model_type, priority = opportunities[0]
        proposal = evolver.generate_evolution_proposal(model_type)
        
        print(f"Proposal ID: {proposal.proposal_id}")
        print(f"Model: {proposal.model_type.value}")
        print(f"Strategy: {proposal.strategy.value}")
        print(f"Description: {proposal.description}")
        print(f"Expected Improvement: {proposal.expected_improvement:.1%}")
        print(f"Confidence: {proposal.confidence:.1%}")
        print()
        print("Evidence:")
        for evidence in proposal.evidence:
            print(f"  - {evidence}")
        print()
    
    # Show evolution stats
    print("D. Evolution Statistics")
    print("-" * 80)
    
    stats = evolver.get_evolution_stats()
    print(f"Total Proposals: {stats['total_proposals']}")
    print(f"Successful: {stats['successful_evolutions']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Models Tracked: {stats['models_tracked']}")
    print()


async def demo_cross_system_learning():
    """Demonstrate cross-system learning"""
    
    print("\n" + "=" * 80)
    print("CROSS-SYSTEM LEARNING DEMONSTRATION")
    print("=" * 80)
    print()
    
    from trading_bot.unified_evolution import SystemIntegrator, SystemType
    
    integrator = SystemIntegrator()
    
    # Register systems
    print("A. System Registration")
    print("-" * 80)
    
    for system_type in [SystemType.AAMIS_V3, SystemType.TAMIC, SystemType.ADAPTIVE_SYSTEMS]:
        integrator.register_system(system_type, None)
        print(f"✓ {system_type.value} registered")
    print()
    
    # Discover transferable knowledge
    print("B. Knowledge Discovery")
    print("-" * 80)
    
    knowledge = integrator.discover_transferable_knowledge(SystemType.AAMIS_V3)
    print(f"Transferable knowledge from AAMIS v3:")
    for item in knowledge:
        print(f"  Type: {item['type']}")
        print(f"  Description: {item['description']}")
        print(f"  Applicable to: {[s.value for s in item['applicable_to']]}")
        print()
    
    # Perform knowledge transfer
    print("C. Knowledge Transfer")
    print("-" * 80)
    
    learning = integrator.transfer_knowledge(
        SystemType.AAMIS_V3,
        SystemType.ADAPTIVE_SYSTEMS,
        'pattern',
        {'patterns': ['trend', 'reversal', 'breakout']}
    )
    
    if learning:
        print(f"Transfer ID: {learning.learning_id}")
        print(f"Source: {learning.source_system.value}")
        print(f"Target: {learning.target_system.value}")
        print(f"Type: {learning.knowledge_type}")
        print(f"Method: {learning.transfer_method}")
        print(f"Success: {learning.success}")
        print(f"Improvement: {learning.improvement:.3f}")
    print()
    
    # Show integration stats
    print("D. Integration Statistics")
    print("-" * 80)
    
    stats = integrator.get_integration_stats()
    print(f"Total Transfers: {stats['total_transfers']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Systems Registered: {stats['systems_registered']}")
    print(f"Active Integrations: {stats['active_integrations']}")
    print()


if __name__ == "__main__":
    print("\nStarting Unified Evolution System Demo...\n")
    
    # Run main demo
    asyncio.run(demo_unified_evolution())
    
    # Run detailed demos
    asyncio.run(demo_model_evolution())
    asyncio.run(demo_cross_system_learning())
    
    print("\nDemo completed successfully!")
    print("\nTo use in your trading bot:")
    print("  from trading_bot.unified_evolution import quick_start_unified")
    print("  orchestrator = await quick_start_unified({'auto_start': True})")
    print("  orchestrator.register_aamis_v3(your_aamis_system)")
    print("  orchestrator.register_tamic(your_tamic_system)")
    print("  # ... register other systems")
