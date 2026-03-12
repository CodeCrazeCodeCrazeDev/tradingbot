"""
Market Intent Decomposition Engine (MIDE) - Demo

Demonstrates the causal market cognition layer that decomposes
market moments into probability-weighted mixtures of latent participant intents.

This is NOT a prediction engine.
This is NOT an indicator system.
MIDE infers WHY price is behaving the way it is—not just how.
"""

import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.deepchart import (
    # MIDE Core
    IntentOrchestrator,
    IntentState,
    IntentSimplex,
    IntentPhase,
    IntentGuidance,
    MIDEConfig,
    INTENT_NAMES,
    INTENT_COLORS,
    create_mide,
    quick_start_mide,
)


def generate_synthetic_market_data(n_bars: int = 200, scenario: str = 'mixed'):
    """
    Generate synthetic market data for different scenarios.
    
    Scenarios:
    - 'urgent': Simulates urgent directional flow
    - 'passive': Simulates passive accumulation
    - 'mechanical': Simulates algorithmic TWAP
    - 'exploitative': Simulates market making
    - 'noise': Simulates random retail flow
    - 'mixed': Mix of all scenarios
    """
    np.random.seed(42)
    
    data = []
    price = 50000.0
    
    for i in range(n_bars):
        # Determine scenario for this bar
        if scenario == 'mixed':
            phase = i // 40  # Change every 40 bars
            current_scenario = ['urgent', 'passive', 'mechanical', 'exploitative', 'noise'][phase % 5]
        else:
            current_scenario = scenario
        
        # Generate data based on scenario
        if current_scenario == 'urgent':
            # Large trades, crossing spread, clustered arrivals
            volume = np.random.exponential(200) + 100
            price_change = np.random.choice([-1, 1]) * volume * 0.0001
            spread = 5.0 + np.random.exponential(2)
            
        elif current_scenario == 'passive':
            # Small trades, patient execution, persistent imbalance
            volume = np.random.uniform(10, 50)
            price_change = np.random.normal(0, 0.5)
            spread = 3.0 + np.random.uniform(0, 1)
            
        elif current_scenario == 'mechanical':
            # Regular intervals, clustered sizes
            volume = 100.0 + np.random.choice([0, 0, 0, 10, -10])  # Clustered
            price_change = np.random.normal(0, 1)
            spread = 4.0
            
        elif current_scenario == 'exploitative':
            # Spread-sensitive, mean-reverting
            volume = np.random.uniform(50, 150)
            price_change = -np.sign(price - 50000) * np.random.uniform(0, 2)
            spread = 8.0 + np.random.exponential(3)
            
        else:  # noise
            # Random everything
            volume = np.random.exponential(50)
            price_change = np.random.normal(0, 3)
            spread = 5.0 + np.random.exponential(2)
        
        price += price_change
        bid = price - spread / 2
        ask = price + spread / 2
        
        # Random bid/ask sizes
        bid_size = np.random.exponential(100)
        ask_size = np.random.exponential(100)
        
        # Add imbalance for passive scenario
        if current_scenario == 'passive':
            bid_size *= 1.5  # Persistent bid pressure
        
        data.append({
            'price': price,
            'volume': volume,
            'bid': bid,
            'ask': ask,
            'bid_size': bid_size,
            'ask_size': ask_size,
            'timestamp': time.time() + i * 0.1,
            'scenario': current_scenario,
        })
    
    return data


def print_intent_state(state: IntentState, bar_idx: int):
    """Pretty print intent state."""
    pi = state.simplex.to_array()
    
    print(f"\n{'='*60}")
    print(f"Bar {bar_idx}: Intent Decomposition")
    print(f"{'='*60}")
    
    # Print simplex as bar chart
    print("\nIntent Mixture:")
    for i, name in enumerate(INTENT_NAMES):
        bar_len = int(pi[i] * 40)
        bar = '█' * bar_len + '░' * (40 - bar_len)
        phase = state.get_intent_phase(name).name
        print(f"  {name:15s} [{bar}] {pi[i]:.2f} ({phase})")
    
    # Print dominant
    print(f"\n  Dominant: {state.dominant_intent.upper()} "
          f"(conf={state.confidence:.2f}, stab={state.stability_score:.2f})")
    
    # Print momentum
    print(f"\n  Momentum: {state.momentum.values}")
    print(f"  Persistence: {state.persistence.values}")
    print(f"  Exhaustion: {state.exhaustion.values}")
    
    # Print transition
    if state.transition_type.name != 'STABLE':
        print(f"\n  ⚠️ TRANSITION: {state.transition_type.name}")


def print_guidance(guidance: IntentGuidance):
    """Pretty print strategy guidance."""
    print(f"\n{'─'*60}")
    print("Strategy Guidance:")
    print(f"{'─'*60}")
    
    # Entry
    entry_icon = '✅' if guidance.should_enter else '❌'
    print(f"\n  Entry: {entry_icon} {guidance.entry_reason}")
    if guidance.should_enter:
        print(f"         Confidence: {guidance.entry_confidence:.2f}")
    
    # Exit
    if guidance.should_exit:
        print(f"\n  Exit: ⚠️ {guidance.exit_reason}")
        print(f"        Urgency: {guidance.exit_urgency:.2f}")
    
    # Sizing
    print(f"\n  Size Multiplier: {guidance.size_multiplier:.2f}x")
    print(f"  Reason: {guidance.size_reason}")
    
    # Execution
    print(f"\n  Execution: {guidance.execution_algo}")
    print(f"  Urgency: {guidance.execution_urgency:.2f}")
    print(f"  Max Spread Cross: {guidance.max_spread_cross_bps:.1f} bps")


def run_demo():
    """Run the MIDE demo."""
    print("\n" + "="*70)
    print("   MARKET INTENT DECOMPOSITION ENGINE (MIDE) - DEMO")
    print("   Causal Market Cognition Layer for AlphaAlgo")
    print("="*70)
    
    # Create MIDE orchestrator
    print("\n[1] Initializing MIDE...")
    config = MIDEConfig(
        feature_window=64,
        hidden_dim=32,
        use_tcn=True,
        use_gru=True,
        use_attention=True,
    )
    mide = IntentOrchestrator(config)
    print("    ✓ MIDE initialized")
    
    # Generate synthetic data
    print("\n[2] Generating synthetic market data (mixed scenario)...")
    data = generate_synthetic_market_data(n_bars=200, scenario='mixed')
    print(f"    ✓ Generated {len(data)} bars")
    
    # Process data
    print("\n[3] Processing market data through MIDE...")
    
    states = []
    for i, bar in enumerate(data):
        state = mide.update(
            price=bar['price'],
            volume=bar['volume'],
            bid=bar['bid'],
            ask=bar['ask'],
            bid_size=bar['bid_size'],
            ask_size=bar['ask_size'],
            timestamp=bar['timestamp']
        )
        states.append(state)
        
        # Print every 40 bars
        if i > 0 and i % 40 == 0:
            print_intent_state(state, i)
            
            # Get guidance
            guidance = mide.get_guidance(
                signal_direction='long',
                signal_strength=0.6
            )
            print_guidance(guidance)
    
    # Print final metrics
    print("\n" + "="*70)
    print("   PERFORMANCE METRICS")
    print("="*70)
    
    metrics = mide.get_metrics()
    print(f"\n  Avg Inference Latency: {metrics.avg_inference_latency_ms:.2f} ms")
    print(f"  Avg Feature Extraction: {metrics.avg_feature_extraction_ms:.2f} ms")
    print(f"  Avg Total Latency: {metrics.avg_total_latency_ms:.2f} ms")
    print(f"  Updates/Second: {metrics.updates_per_second:.1f}")
    print(f"  Avg Confidence: {metrics.avg_confidence:.2f}")
    print(f"  Avg Stability: {metrics.avg_stability:.2f}")
    print(f"  Transition Rate: {metrics.transition_rate:.2f} per 100 bars")
    
    # Print phase summary
    print("\n" + "="*70)
    print("   INTENT PHASES (Final State)")
    print("="*70)
    
    phases = mide.get_all_phases()
    for intent, phase in phases.items():
        print(f"  {intent:15s}: {phase.name}")
    
    # Get visualization data
    print("\n" + "="*70)
    print("   VISUALIZATION DATA")
    print("="*70)
    
    viz = mide.get_visualization(lookback=50)
    print(f"\n  Ribbon slices: {len(viz.ribbon_slices)}")
    print(f"  Transitions: {len(viz.transition_markers)}")
    print(f"  Momentum arrows: {len(viz.momentum_arrows)}")
    
    if viz.transition_markers:
        print("\n  Recent transitions:")
        for bar, from_intent, to_intent in viz.transition_markers[-5:]:
            print(f"    Bar {bar}: {from_intent} → {to_intent}")
    
    print("\n" + "="*70)
    print("   DEMO COMPLETE")
    print("="*70)
    print("\nMIDE successfully decomposed market flow into participant intents.")
    print("The 5 canonical intents detected:")
    print("  1. Urgent Directional - Informed traders with time pressure")
    print("  2. Passive Accumulation - Patient institutional flow")
    print("  3. Mechanical Flow - Algorithmic rebalancing (TWAP/VWAP)")
    print("  4. Exploitative - Market makers, stat-arb")
    print("  5. Noise - Retail, uninformed flow")
    print("\nThis is NOT prediction. This is causal inference of WHY price moves.")


if __name__ == '__main__':
    run_demo()
