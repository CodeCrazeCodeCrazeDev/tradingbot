"""
AlphaAlgo 10-Layer Cognitive Architecture - Demo Script

This script demonstrates the complete cognitive architecture in action,
showing how all 10 layers work together to make trading decisions.

Run this to see AlphaAlgo's AGI-level trading intelligence!
"""

import numpy as np
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore


def create_sample_market_data(scenario='normal'):
    """Create sample market data for different scenarios"""
    dates = pd.date_range(start='2025-01-01', periods=200, freq='1H')
    np.random.seed(42)
    
    base_price = 1.1000
    
    if scenario == 'normal':
        # Normal market - low volatility
        prices = base_price + np.cumsum(np.random.normal(0, 0.0005, 200))
    elif scenario == 'volatile':
        # Volatile market - high volatility
        prices = base_price + np.cumsum(np.random.normal(0, 0.002, 200))
    elif scenario == 'extreme':
        # Extreme market - very high volatility
        prices = base_price + np.cumsum(np.random.normal(0, 0.005, 200))
    elif scenario == 'trending':
        # Trending market - strong uptrend
        trend = np.linspace(0, 0.01, 200)
        prices = base_price * (1 + trend) + np.cumsum(np.random.normal(0, 0.0003, 200))
    elif scenario == 'ranging':
        # Ranging market - sideways
        prices = base_price + np.sin(np.linspace(0, 4*np.pi, 200)) * 0.0005
    else:
        # Transitioning market - regime change
        prices = np.concatenate([
            base_price + np.cumsum(np.random.normal(0, 0.0005, 100)),
            base_price + np.cumsum(np.random.normal(0, 0.002, 100))
        ])
    
    market_data = pd.DataFrame({
        'open': prices + np.random.normal(0, 0.0002, 200),
        'high': prices + np.random.normal(0.0003, 0.0002, 200),
        'low': prices + np.random.normal(-0.0003, 0.0002, 200),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 200)
    }, index=dates)
    
    return market_data


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print formatted section"""
    print(f"\n--- {text} ---")


def demo_single_scenario(cognitive_core, scenario_name):
    """Demonstrate cognitive core on a single scenario"""
    print_header(f"SCENARIO: {scenario_name.upper()} MARKET")
    
    # Create market data
    market_data = create_sample_market_data(scenario_name)
    
    print(f"\nMarket Data:")
    print(f"  Period: {market_data.index[0]} to {market_data.index[-1]}")
    print(f"  Bars: {len(market_data)}")
    print(f"  Price Range: {market_data['low'].min():.5f} - {market_data['high'].max():.5f}")
    print(f"  Current Price: {market_data['close'].iloc[-1]:.5f}")
    
    # Make decision using all 10 layers
    print("\nProcessing through 10-Layer Cognitive Architecture...")
    decision = cognitive_core.make_decision(market_data)
    
    # Display results
    print_section("DECISION OUTPUT")
    print(f"  Action: {decision.action}")
    print(f"  Confidence: {decision.confidence:.2%}")
    print(f"  Position Size: {decision.position_size:.4f}")
    print(f"  Stop Loss: {decision.stop_loss:.5f}")
    print(f"  Take Profit: {decision.take_profit:.5f}")
    print(f"  Risk Score: {decision.risk_score:.2%}")
    print(f"  Expected Return: {decision.expected_return:.2%}")
    print(f"  Time Horizon: {decision.time_horizon}")
    
    print_section("COGNITIVE STATE")
    cs = decision.cognitive_state
    print(f"  Market Regime: {cs.market_regime.value.upper()}")
    print(f"  Regime Confidence: {cs.regime_confidence:.2%}")
    print(f"  Integration Mode: {cs.integration_mode}")
    print(f"  Consensus Score: {cs.consensus_score:.2%}")
    print(f"  System Health: {cs.system_health:.2%}")
    print(f"  Safety Status: {cs.safety_status}")
    print(f"  Evolution Cycle: {cs.evolution_cycle}")
    
    print_section("REASONING")
    print(decision.reasoning)
    
    return decision


def demo_all_scenarios():
    """Demonstrate all market scenarios"""
    print_header("ALPHAALGO 10-LAYER COGNITIVE ARCHITECTURE DEMO")
    print("\nThis demo shows how AlphaAlgo's cognitive architecture")
    print("processes different market conditions through all 10 layers:")
    print("\n  Layer 1: Market State Detection")
    print("  Layer 2: Adaptive Integration")
    print("  Layer 3: Multi-Agent Coordination")
    print("  Layer 4: Neuro-Symbolic Reasoning")
    print("  Layer 5: Advanced RL")
    print("  Layer 6: Multi-Modal Fusion")
    print("  Layer 7: Self-Healing Supervisor")
    print("  Layer 8: Quantum & Simulation")
    print("  Layer 9: Explainability Interface")
    print("  Layer 10: Continuous Evolution")
    
    # Initialize cognitive core
    print("\nInitializing AlphaAlgo Cognitive Core...")
    cognitive_core = AlphaAlgoCognitiveCore(config={
        'base_dir': 'alphaalgo_cognitive_demo'
    })
    print("Cognitive Core initialized successfully!")
    
    # Test scenarios
    scenarios = [
        'normal',
        'volatile',
        'extreme',
        'trending',
        'ranging',
        'transitioning'
    ]
    
    decisions = {}
    
    for scenario in scenarios:
        decision = demo_single_scenario(cognitive_core, scenario)
        decisions[scenario] = decision
        
        # Pause between scenarios
        input("\nPress Enter to continue to next scenario...")
    
    # Summary
    print_header("SUMMARY OF ALL SCENARIOS")
    
    print("\n{:<15} {:<10} {:<12} {:<20} {:<15}".format(
        "Scenario", "Action", "Confidence", "Regime", "Integration Mode"
    ))
    print("-" * 80)
    
    for scenario, decision in decisions.items():
        print("{:<15} {:<10} {:<12} {:<20} {:<15}".format(
            scenario.capitalize(),
            decision.action,
            f"{decision.confidence:.1%}",
            decision.cognitive_state.market_regime.value,
            decision.cognitive_state.integration_mode
        ))
    
    # System status
    print_section("SYSTEM STATUS")
    status = cognitive_core.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print_header("DEMO COMPLETE")
    print("\nAlphaAlgo's 10-Layer Cognitive Architecture successfully")
    print("processed all market scenarios with full explainability!")
    print("\nNext steps:")
    print("  1. Review decision logs in: alphaalgo_cognitive_demo/decisions/")
    print("  2. Integrate with your trading loop")
    print("  3. Start paper trading")
    print("  4. Deploy to production")
    print("\n" + "=" * 80)


def demo_quick_test():
    """Quick test of cognitive core"""
    print_header("QUICK TEST - ALPHAALGO COGNITIVE CORE")
    
    # Initialize
    print("\nInitializing...")
    cognitive_core = AlphaAlgoCognitiveCore()
    
    # Create test data
    print("Creating test market data...")
    market_data = create_sample_market_data('trending')
    
    # Make decision
    print("Making decision through all 10 layers...")
    decision = cognitive_core.make_decision(market_data)
    
    # Display
    print("\n" + "=" * 80)
    print("DECISION RESULT")
    print("=" * 80)
    print(f"\nAction: {decision.action}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Position Size: {decision.position_size:.4f}")
    print(f"\nMarket Regime: {decision.cognitive_state.market_regime.value}")
    print(f"Integration Mode: {decision.cognitive_state.integration_mode}")
    print(f"System Health: {decision.cognitive_state.system_health:.2%}")
    
    print("\n" + "=" * 80)
    print("QUICK TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AlphaAlgo Cognitive Core Demo')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--scenario', type=str, choices=['normal', 'volatile', 'extreme', 'trending', 'ranging', 'transitioning'],
                       help='Run specific scenario only')
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            demo_quick_test()
        elif args.scenario:
            cognitive_core = AlphaAlgoCognitiveCore()
            demo_single_scenario(cognitive_core, args.scenario)
        else:
            demo_all_scenarios()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
