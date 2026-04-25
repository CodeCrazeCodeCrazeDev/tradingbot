"""
Capability Distillation Demo
============================

Demonstrates the autonomous capability distillation system.

This system:
1. Observes frontier models
2. Benchmarks them by task
3. Extracts useful behaviors
4. Inverts weaknesses into controls
5. Validates in sandbox
6. Deploys selectively
7. Monitors performance
8. Keeps only what improves the global objective
"""

import asyncio
import logging
from trading_bot.neuros_evolution.capability_distillation import (
    CapabilityDistillationSystem,
    create_distillation_system
)

# Setup logging
logging.basicConfig(level=logging.INFO)


def custom_global_objective(metrics: dict) -> float:
    """
    Define your global objective function.
    This determines whether a distilled capability is retained.
    """
    # Weight factors for trading bot performance
    weights = {
        'throughput': 0.15,        # Signals processed per second
        'latency_p95': -0.20,      # Response time (lower is better)
        'error_rate': -0.30,       # Trading errors (lower is better)
        'resource_efficiency': 0.15,
        'pnl_contribution': 0.35,   # Profit/loss impact
    }
    
    score = 0.0
    for metric, weight in weights.items():
        value = metrics.get(metric, 0)
        if metric == 'latency_p95':
            # Normalize latency: 0-100ms -> 1-0
            value = max(0, 1 - value / 100)
        score += value * weight
    
    return score


async def demo_single_cycle():
    """Run a single distillation cycle"""
    
    # Create the distillation system
    system = create_distillation_system(
        sandbox_path="./sandbox",
        global_objective_fn=custom_global_objective
    )
    
    # Define benchmark tasks for trading
    def eval_signal_generation(result):
        """Evaluate signal generation quality"""
        confidence = result.get('confidence', 0)
        return confidence
    
    system.define_benchmark_task(
        task_name="signal_generation",
        category="trading",
        evaluation_fn=eval_signal_generation,
        test_cases=[
            {'task_type': 'signal_generation', 'market_condition': 'trending'},
            {'task_type': 'signal_generation', 'market_condition': 'ranging'},
            {'task_type': 'signal_generation', 'market_condition': 'volatile'},
        ]
    )
    
    # Simulated interaction data from a frontier model
    interaction_data = [
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
    ]
    
    # Simulated failure cases for control generation
    failure_cases = [
        {'type': 'timeout', 'description': 'Slow response during high volatility'},
        {'type': 'incorrect', 'description': 'False breakout signal'},
    ]
    
    # Run the full distillation cycle
    results = await system.run_full_cycle(
        model_id="gpt-4-trading",
        provider="openai",
        interaction_data=interaction_data,
        task_names=["signal_generation"],
        failure_cases=failure_cases,
        deployment_strategy="gradual"
    )
    
    print("\n=== Distillation Cycle Results ===")
    print(f"Model ID: {results.get('model_id')}")
    print(f"Status: {results.get('status')}")
    
    if 'steps' in results:
        for step, data in results['steps'].items():
            print(f"\n{step.upper()}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    # Generate system report
    report = system.get_system_report()
    print("\n=== System Report ===")
    print(f"Total Behaviors Extracted: {report['extractor']['total_behaviors']}")
    print(f"Total Controls Created: {report['inverter']['total_controls']}")
    print(f"Sandbox Pass Rate: {report['sandbox']['pass_rate']:.2%}")
    print(f"Active Deployments: {report['deployer']['active_deployments']}")
    
    return results


async def demo_continuous_distillation():
    """Demonstrate continuous distillation (would run indefinitely)"""
    
    system = create_distillation_system()
    
    # Define models to observe
    models_to_observe = [
        {
            'model_id': 'gpt-4-trading-v1',
            'provider': 'openai',
            'interaction_data': [],  # Would be populated with real data
            'task_names': ['signal_generation', 'risk_assessment'],
            'failure_cases': [],
            'strategy': 'gradual'
        },
        {
            'model_id': 'claude-trading-v1',
            'provider': 'anthropic',
            'interaction_data': [],
            'task_names': ['signal_generation', 'market_analysis'],
            'failure_cases': [],
            'strategy': 'cautious'
        },
    ]
    
    # Run for a short time (normally runs forever)
    # This is commented out as it would run indefinitely:
    # await system.run_continuous_distillation(
    #     models_to_observe=models_to_observe,
    #     check_interval_minutes=60
    # )
    
    print("Continuous distillation configured (not running to avoid infinite loop)")


async def main():
    """Main demo"""
    print("=" * 60)
    print("AUTONOMOUS CAPABILITY DISTILLATION DEMO")
    print("=" * 60)
    
    await demo_single_cycle()
    # await demo_continuous_distillation()  # Would run continuously


if __name__ == "__main__":
    asyncio.run(main())
