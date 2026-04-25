"""
Meta-Intelligence Layer Demo
============================

Demonstrates the complete model-agnostic meta-intelligence layer
that continuously learns to outperform any single AI model.

Architecture:
1. Capability Distillation - Extract behaviors from frontier models
2. Capability Registry - Store and track performance
3. Task Router - Intelligent routing with learned strategies
4. Behavior Synthesis - Ensemble and chain capabilities
5. Meta-Learning - Continuously improve routing and synthesis
6. Orchestrator - Unified interface
"""

import asyncio
import logging
from datetime import datetime

# Import the meta-intelligence layer
from trading_bot.neuros_evolution import (
    create_meta_intelligence_layer,
    MetaIntelligenceOrchestrator,
    RoutingStrategy
)

logging.basicConfig(level=logging.INFO)


# ==========================================
# 1. Define Your Global Objective
# ==========================================

def trading_global_objective(metrics: dict) -> float:
    """
    Define what "better" means for your trading system.
    The meta-intelligence layer will only retain capabilities
    that improve this objective.
    """
    # Weights for trading performance
    weights = {
        'pnl': 0.40,              # Profit/loss contribution
        'sharpe_ratio': 0.25,     # Risk-adjusted returns
        'win_rate': 0.15,         # Signal accuracy
        'latency_ms': -0.10,      # Execution speed (lower is better)
        'drawdown': -0.10,        # Max drawdown (lower is better)
    }
    
    score = 0.0
    for metric, weight in weights.items():
        value = metrics.get(metric, 0)
        # Normalize latency: 0-100ms -> 1-0
        if metric == 'latency_ms':
            value = max(0, 1 - value / 100)
        # Normalize drawdown: 0-0.5 -> 1-0
        elif metric == 'drawdown':
            value = max(0, 1 - value / 0.5)
        
        score += value * weight
    
    return score


# ==========================================
# 2. Define Capability Implementations
# ==========================================

async def signal_generation_v1(input_data: dict) -> dict:
    """Implementation of distilled signal generation capability"""
    # Simulated implementation
    symbol = input_data.get('symbol', 'UNKNOWN')
    
    # Apply the distilled pattern
    signal = {
        'symbol': symbol,
        'signal': 'BUY' if input_data.get('momentum', 0) > 0.5 else 'SELL',
        'confidence': 0.75 + (input_data.get('volatility', 0) * 0.2),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return signal


async def risk_assessment_v1(input_data: dict) -> dict:
    """Implementation of distilled risk assessment capability"""
    position_size = input_data.get('position_size', 1000)
    volatility = input_data.get('volatility', 0.1)
    
    risk_score = min(1.0, (position_size * volatility) / 10000)
    
    return {
        'risk_score': risk_score,
        'max_position': position_size * (1 - risk_score),
        'stop_loss_pct': volatility * 2,
        'timestamp': datetime.utcnow().isoformat()
    }


# ==========================================
# 3. Main Demo
# ==========================================

async def demo_basic_usage():
    """Demonstrate basic task processing"""
    print("\n" + "="*60)
    print("BASIC USAGE DEMO")
    print("="*60)
    
    # Create the meta-intelligence layer
    layer = create_meta_intelligence_layer(
        data_dir="./demo_meta_intelligence",
        global_objective_fn=trading_global_objective
    )
    
    await layer.start()
    
    # Register some capability implementations
    layer.register_implementation("sig_gen_v1", signal_generation_v1)
    layer.register_implementation("risk_assess_v1", risk_assessment_v1)
    
    # Process a signal generation task
    result = await layer.process_task(
        task_type="generate_signal",
        input_data={
            'symbol': 'BTC/USD',
            'timeframe': '1h',
            'momentum': 0.7,
            'volatility': 0.15
        },
        task_category="signal_generation",
        tags=['crypto', 'hourly'],
        timeout_ms=2000
    )
    
    print(f"\nTask ID: {result.task_id}")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Routing Strategy: {result.routing.strategy_used}")
    print(f"Confidence: {result.routing.confidence:.3f}")
    print(f"Latency: {result.execution.latency_ms:.1f}ms")
    
    # Get system health
    health = layer.get_system_health()
    print(f"\nSystem Status: {health.status}")
    print(f"Active Capabilities: {health.registry_health['active_capabilities']}")
    
    await layer.stop()


async def demo_capability_distillation():
    """Demonstrate capability distillation from frontier models"""
    print("\n" + "="*60)
    print("CAPABILITY DISTILLATION DEMO")
    print("="*60)
    
    layer = create_meta_intelligence_layer(
        data_dir="./demo_distillation",
        global_objective_fn=trading_global_objective
    )
    
    await layer.start()
    
    # Simulate interaction data from GPT-4
    gpt4_interactions = [
        {
            'task': 'Generate buy signal for BTC/USD',
            'response': 'Signal: BUY, Confidence: 0.87, Reason: Breakout detected',
            'task_type': 'signal_generation',
            'reasoning': ['analyze_trend', 'detect_breakout', 'calculate_confidence']
        },
        {
            'task': 'Generate sell signal for ETH/USD',
            'response': 'Signal: SELL, Confidence: 0.92, Reason: Resistance hit',
            'task_type': 'signal_generation',
            'reasoning': ['analyze_trend', 'identify_resistance', 'calculate_confidence']
        },
        {
            'task': 'Generate buy signal for SOL/USD',
            'response': 'Signal: BUY, Confidence: 0.78, Reason: Support bounce',
            'task_type': 'signal_generation',
            'reasoning': ['identify_support', 'confirm_bounce', 'calculate_confidence']
        }
    ]
    
    # Failure cases for control generation
    failure_cases = [
        {'type': 'timeout', 'description': 'Slow response during high volatility'},
        {'type': 'incorrect', 'description': 'False breakout signal in ranging market'},
    ]
    
    # Run distillation
    print("\nRunning distillation cycle...")
    results = await layer.distill_from_model(
        model_id="gpt-4-trading",
        provider="openai",
        interaction_data=gpt4_interactions,
        task_names=["signal_generation"],
        failure_cases=failure_cases,
        deployment_strategy="gradual"
    )
    
    print(f"\nDistillation Status: {results.get('status')}")
    
    if 'steps' in results:
        for step, data in results['steps'].items():
            print(f"\n{step.upper()}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    # Check what was registered
    health = layer.get_system_health()
    print(f"\nTotal Capabilities: {health.registry_health['total_capabilities']}")
    
    await layer.stop()


async def demo_behavior_synthesis():
    """Demonstrate behavior synthesis (ensemble/chaining)"""
    print("\n" + "="*60)
    print("BEHAVIOR SYNTHESIS DEMO")
    print("="*60)
    
    layer = create_meta_intelligence_layer(
        data_dir="./demo_synthesis",
        global_objective_fn=trading_global_objective
    )
    
    await layer.start()
    
    # Register implementations for synthesized capabilities
    async def preprocessor(input_data: dict) -> dict:
        return {'processed': True, 'features': input_data.get('raw_data', {})}
    
    async def analyzer(input_data: dict) -> dict:
        return {'analysis': 'bullish', 'confidence': 0.8}
    
    async def postprocessor(input_data: dict) -> dict:
        prev = input_data.get('previous_output', {})
        return {
            'final_signal': prev.get('analysis', 'neutral'),
            'confidence': prev.get('confidence', 0.5) * 1.1
        }
    
    # Register to registry first
    layer.register_implementation("preprocessor_v1", preprocessor)
    layer.register_implementation("analyzer_v1", analyzer)
    layer.register_implementation("postprocessor_v1", postprocessor)
    
    # Create a chain: preprocess -> analyze -> postprocess
    print("\nCreating chain synthesis...")
    chain_id = await layer.create_chain_capability(
        name="complete_signal_pipeline",
        task_category="signal_generation",
        capability_ids=["preprocessor_v1", "analyzer_v1", "postprocessor_v1"],
        stage_names=["extract", "analyze", "format"]
    )
    
    print(f"Created chain: {chain_id}")
    
    # Validate the chain
    test_cases = [
        {'input': {'raw_data': {'price': 50000, 'volume': 1000}}},
        {'input': {'raw_data': {'price': 48000, 'volume': 800}}}
    ]
    
    validation = await layer.validate_and_register_synthesis(
        synthesis_id=chain_id,
        test_cases=test_cases
    )
    
    print(f"\nValidation Result: {validation['status']}")
    print(f"Accuracy: {validation['accuracy']:.3f}")
    print(f"Registered: {validation.get('registered_capability_id', 'N/A')}")
    
    # Execute the chain
    if validation['status'] == 'validated':
        print("\nExecuting chain...")
        result = await layer.execute_synthesized_capability(
            synthesis_id=chain_id,
            input_data={'raw_data': {'price': 52000, 'volume': 1500}},
            timeout_ms=3000
        )
        
        print(f"Chain Output: {result['output']}")
        print(f"Success: {result['success']}")
        print(f"Latency: {result['latency_ms']:.1f}ms")
    
    await layer.stop()


async def demo_meta_learning():
    """Demonstrate meta-learning optimization"""
    print("\n" + "="*60)
    print("META-LEARNING DEMO")
    print("="*60)
    
    layer = create_meta_intelligence_layer(
        data_dir="./demo_meta_learning",
        global_objective_fn=trading_global_objective
    )
    
    await layer.start()
    
    # Generate some routing history
    print("\nSimulating routing activity...")
    for i in range(20):
        await layer.process_task(
            task_type=f"task_{i % 5}",
            input_data={'test': i},
            task_category="signal_generation" if i % 2 == 0 else "risk_assessment"
        )
    
    # Run meta-learning cycle
    print("\nRunning meta-learning cycle...")
    cycle_result = await layer.run_meta_learning_cycle()
    
    print(f"\nCycle ID: {cycle_result['cycle_id']}")
    print(f"Status: {cycle_result['status']}")
    print(f"Improvements Made: {cycle_result['improvements_made']}")
    print(f"Discoveries: {cycle_result['discoveries']}")
    print(f"Performance Delta: {cycle_result['performance_delta']:+.4f}")
    
    if cycle_result['improvements']:
        print("\nImprovements:")
        for imp in cycle_result['improvements']:
            print(f"  - {imp['type']}: {imp.get('reason', 'N/A')}")
    
    # Get learning summary
    summary = layer.meta_learner.get_learning_summary()
    print(f"\nTotal Learning Cycles: {summary['total_cycles']}")
    print(f"Total Improvements: {summary['total_improvements']}")
    print(f"Known Categories: {summary['known_categories']}")
    
    await layer.stop()


async def demo_comprehensive_report():
    """Generate comprehensive system report"""
    print("\n" + "="*60)
    print("COMPREHENSIVE SYSTEM REPORT")
    print("="*60)
    
    layer = create_meta_intelligence_layer(
        data_dir="./demo_comprehensive",
        global_objective_fn=trading_global_objective
    )
    
    await layer.start()
    
    # Simulate some activity
    for i in range(10):
        await layer.process_task(
            task_type="generate_signal",
            input_data={'symbol': f'SYM{i}', 'momentum': 0.5 + i * 0.05},
            task_category="signal_generation"
        )
    
    # Get comprehensive report
    report = layer.get_comprehensive_report()
    
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"System Status: {report['system_status']}")
    
    print(f"\nCapabilities:")
    print(f"  Total: {report['capabilities']['total']}")
    print(f"  Active: {report['capabilities']['active']}")
    
    print(f"\nRouting:")
    print(f"  Total Routes: {report['routing']['total_routes']}")
    print(f"  Success Rate: {report['routing']['success_rate']:.2%}")
    print(f"  Exploration Rate: {report['routing']['exploration_rate']:.2%}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    # Export state
    layer.export_state("./demo_comprehensive/state_export.json")
    print("\nState exported to ./demo_comprehensive/state_export.json")
    
    await layer.stop()


async def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("META-INTELLIGENCE LAYER DEMONSTRATION")
    print("="*60)
    print("\nThis demonstrates a model-agnostic system that:")
    print("1. Observes frontier models and extracts their best behaviors")
    print("2. Stores capabilities in a registry with performance tracking")
    print("3. Routes tasks intelligently to the best option")
    print("4. Synthesizes behaviors into ensembles and chains")
    print("5. Continuously learns and improves its own performance")
    print("6. Only keeps what improves YOUR global objective")
    
    await demo_basic_usage()
    await demo_capability_distillation()
    await demo_behavior_synthesis()
    await demo_meta_learning()
    await demo_comprehensive_report()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nThe meta-intelligence layer is now ready for:")
    print("- Continuous capability distillation from frontier models")
    print("- Intelligent task routing with learned strategies")
    print("- Behavior synthesis for complex workflows")
    print("- Meta-learning for continuous self-improvement")
    print("- Optimization for your specific trading objectives")


if __name__ == "__main__":
    asyncio.run(main())
