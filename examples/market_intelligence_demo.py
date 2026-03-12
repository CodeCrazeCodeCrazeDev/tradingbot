"""
DeepChart Market Intelligence Demo

Demonstrates all 15 unified market intelligence concepts:
1. Market Micro-Friction Map
2. Latent Market State Background
3. Time-to-Move Predictor
4. Synthetic Liquidity Shadows
5. Volume Entropy Tracker
6. Market Memory Decay Map
7. Execution Quality Forecast
8. Micro-Trend Vectors
9. Liquidity Vacuum Detector
10. Model Disagreement Heatmap
11. Price Response Curvature Map
12. Learned Support/Resistance
13. Information Flow Speedometer
14. Strategy-Specific Views
15. Confidence-Weighted Overlays

Usage:
    python examples/market_intelligence_demo.py
"""

import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.deepchart import (
    MarketIntelligenceOrchestrator,
    MarketIntelligenceConfig,
    MarketRegime,
    StrategyLens,
    create_market_intelligence,
)


def generate_synthetic_market_data(n_bars: int = 500, seed: int = 42):
    """
    Generate synthetic market data for demonstration.
    
    Creates realistic price action with:
    - Trending periods
    - Ranging periods
    - Volatility expansion/compression
    - Volume patterns
    """
    np.random.seed(seed)
    
    # Base price
    base_price = 50000.0
    
    # Generate returns with regime changes
    returns = []
    volumes = []
    
    regime = 'trending'
    regime_duration = 0
    
    for i in range(n_bars):
        # Regime switching
        regime_duration += 1
        if regime_duration > np.random.randint(50, 150):
            regime = np.random.choice(['trending', 'ranging', 'volatile'])
            regime_duration = 0
        
        # Generate return based on regime
        if regime == 'trending':
            ret = np.random.normal(0.0002, 0.001)  # Positive drift
            vol = np.random.lognormal(5, 0.5)
        elif regime == 'ranging':
            ret = np.random.normal(0, 0.0005)  # No drift
            vol = np.random.lognormal(4, 0.3)
        else:  # volatile
            ret = np.random.normal(0, 0.003)  # High variance
            vol = np.random.lognormal(6, 0.7)
        
        returns.append(ret)
        volumes.append(vol)
    
    # Convert to prices
    prices = [base_price]
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices[1:])
    volumes = np.array(volumes)
    
    # Generate bid/ask
    spreads = np.random.uniform(0.0001, 0.0005, n_bars) * prices
    bids = prices - spreads / 2
    asks = prices + spreads / 2
    
    return prices, volumes, bids, asks


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_basic_usage():
    """Demonstrate basic usage of the market intelligence system."""
    print_section("BASIC USAGE")
    
    # Create orchestrator
    config = MarketIntelligenceConfig(
        friction_levels=20,
        memory_decay_halflife=100,
        latent_dim=8,
        max_inference_ms=5.0,
    )
    
    orchestrator = MarketIntelligenceOrchestrator(config)
    
    # Generate data
    prices, volumes, bids, asks = generate_synthetic_market_data(100)
    
    print(f"Generated {len(prices)} bars of synthetic data")
    print(f"Price range: {prices.min():.2f} - {prices.max():.2f}")
    
    # Process data
    print("\nProcessing market data...")
    
    for i in range(len(prices)):
        intelligence = orchestrator.update(
            symbol="BTCUSDT",
            price=prices[i],
            volume=volumes[i],
            bid=bids[i],
            ask=asks[i],
        )
    
    # Show results
    print(f"\n✓ Processed {len(prices)} bars")
    print(f"✓ Inference latency: {intelligence.inference_latency_ms:.2f}ms")
    print(f"✓ Overall confidence: {intelligence.overall_confidence:.2%}")
    print(f"✓ Market quality: {intelligence.market_quality_score:.2%}")
    print(f"✓ Tradability: {intelligence.tradability_score:.2%}")
    
    return orchestrator, intelligence


def demo_regime_detection(intelligence):
    """Demonstrate latent market state / regime detection."""
    print_section("CONCEPT 2: LATENT MARKET STATE")
    
    state = intelligence.latent_state
    
    print(f"Current Regime: {state.regime.name}")
    print(f"Regime Confidence: {state.regime_confidence:.2%}")
    print(f"Regime Duration: {state.regime_duration_bars} bars")
    print(f"Regime Stability: {state.regime_stability:.2%}")
    print(f"Transition Probability: {state.transition_probability:.2%}")
    print(f"Latent Vector: {state.latent_vector[:4]}... (8-dim)")
    print(f"Regime Color (RGBA): {state.regime_color}")


def demo_time_to_move(intelligence):
    """Demonstrate time-to-move predictor."""
    print_section("CONCEPT 3: TIME-TO-MOVE PREDICTOR")
    
    ttm = intelligence.time_to_move
    
    print(f"Bars to Breakout: {ttm.bars_to_breakout:.1f}")
    print(f"Breakout Confidence: {ttm.confidence_breakout:.2%}")
    print(f"Bars to Reversion: {ttm.bars_to_reversion:.1f}")
    print(f"Reversion Confidence: {ttm.confidence_reversion:.2%}")
    print(f"Compression Score: {ttm.compression_score:.2%}")
    print(f"Energy Buildup: {ttm.energy_buildup:.2%}")
    print(f"Volatility Forecast: {ttm.volatility_forecast:.6f}")


def demo_friction_map(intelligence):
    """Demonstrate micro-friction map."""
    print_section("CONCEPT 1: MICRO-FRICTION MAP")
    
    friction_map = intelligence.friction_map
    
    print(f"Total Friction Points: {len(friction_map)}")
    
    if friction_map:
        # Show top 5 by confidence
        sorted_points = sorted(friction_map, key=lambda x: x.confidence, reverse=True)[:5]
        
        print("\nTop 5 Friction Points:")
        for i, fp in enumerate(sorted_points, 1):
            print(f"  {i}. Price: {fp.price_level:.2f}")
            print(f"     Friction: {fp.friction_coefficient:.2%}")
            print(f"     Zone: {fp.zone_type.name}")
            print(f"     Slippage Est: {fp.slippage_estimate_bps:.1f} bps")
            print(f"     Confidence: {fp.confidence:.2%}")


def demo_liquidity(intelligence):
    """Demonstrate synthetic liquidity and entropy."""
    print_section("CONCEPTS 4-5: LIQUIDITY & ENTROPY")
    
    liq = intelligence.liquidity_map
    ent = intelligence.volume_entropy
    
    print("SYNTHETIC LIQUIDITY:")
    print(f"  Hidden Bid Estimate: {liq.hidden_bid_estimate:.2%}")
    print(f"  Hidden Ask Estimate: {liq.hidden_ask_estimate:.2%}")
    print(f"  Asymmetry Score: {liq.asymmetry_score:+.2f}")
    print(f"  Iceberg Probability: {liq.iceberg_probability:.2%}")
    
    print("\nVOLUME ENTROPY:")
    print(f"  Entropy: {ent.entropy:.3f}")
    print(f"  Information Ratio: {ent.information_ratio:.2%}")
    print(f"  Noise Floor: {ent.noise_floor:.2%}")
    print(f"  Informed Trading Prob: {ent.informed_trading_prob:.2%}")
    print(f"  Volume Clustering: {ent.volume_clustering:.2%}")


def demo_execution_quality(intelligence):
    """Demonstrate execution quality forecast."""
    print_section("CONCEPT 7: EXECUTION QUALITY FORECAST")
    
    exec_forecast = intelligence.execution_forecast
    
    print(f"Expected Slippage: {exec_forecast.expected_slippage_bps:.2f} bps")
    print(f"Fill Probability: {exec_forecast.fill_probability:.2%}")
    print(f"Time to Fill: {exec_forecast.time_to_fill_ms:.0f} ms")
    print(f"Adverse Selection Risk: {exec_forecast.adverse_selection_risk:.2%}")
    print(f"Market Impact: {exec_forecast.market_impact_estimate:.4f}")
    print(f"Execution Risk: {exec_forecast.execution_risk.name}")
    print(f"Optimal Order Size: {exec_forecast.optimal_order_size:.2f}")
    print(f"Confidence: {exec_forecast.confidence:.2%}")


def demo_memory_levels(intelligence):
    """Demonstrate market memory and learned S/R."""
    print_section("CONCEPTS 6 & 12: MEMORY & LEARNED S/R")
    
    memory = intelligence.memory_levels
    learned_sr = intelligence.learned_sr
    
    print(f"MARKET MEMORY LEVELS: {len(memory)}")
    if memory:
        for i, level in enumerate(memory[:5], 1):
            print(f"  {i}. {level.level_type.upper()} @ {level.price:.2f}")
            print(f"     Strength: {level.current_strength:.2%} (decay: {level.strength_decay:.2%})")
            print(f"     Reactions: {level.reaction_count}")
    
    print(f"\nLEARNED S/R LEVELS: {len(learned_sr)}")
    if learned_sr:
        for i, sr in enumerate(learned_sr[:5], 1):
            print(f"  {i}. {sr.level_type.upper()} @ {sr.price:.2f}")
            print(f"     Reaction Prob: {sr.reaction_probability:.2%}")
            print(f"     Confidence: {sr.confidence:.2%}")


def demo_micro_trends(intelligence):
    """Demonstrate micro-trend vectors."""
    print_section("CONCEPT 8: MICRO-TREND VECTORS")
    
    trends = intelligence.micro_trends
    
    print(f"Total Trend Vectors: {len(trends)}")
    
    if trends:
        latest = trends[-1]
        print(f"\nLatest Trend Vector:")
        print(f"  Direction: {latest.direction:+.2f}")
        print(f"  Magnitude: {latest.magnitude:.2%}")
        print(f"  Acceleration: {latest.acceleration:+.4f}")
        print(f"  Divergence: {latest.divergence:+.2f}")
        print(f"  Curl: {latest.curl:+.4f}")
        print(f"  Confidence: {latest.confidence:.2%}")


def demo_vacuums(intelligence):
    """Demonstrate liquidity vacuum detection."""
    print_section("CONCEPT 9: LIQUIDITY VACUUMS")
    
    vacuums = intelligence.liquidity_vacuums
    
    print(f"Detected Vacuums: {len(vacuums)}")
    
    if vacuums:
        for i, v in enumerate(vacuums[:3], 1):
            print(f"  {i}. Range: {v.price_start:.2f} - {v.price_end:.2f}")
            print(f"     Strength: {v.vacuum_strength:.2%}")
            print(f"     Jump Risk: {v.jump_risk:.2%}")
            print(f"     Persistence: {v.persistence} bars")
    else:
        print("  No significant vacuums detected")


def demo_disagreement(intelligence):
    """Demonstrate model disagreement."""
    print_section("CONCEPT 10: MODEL DISAGREEMENT")
    
    disagree = intelligence.model_disagreement
    
    print(f"Disagreement Score: {disagree.disagreement_score:.2%}")
    print(f"Variance: {disagree.variance:.4f}")
    print(f"Entropy: {disagree.entropy:.3f}")
    print(f"Confidence Adjusted: {disagree.confidence_adjusted:.2%}")
    
    print("\nModel Predictions:")
    for model, pred in disagree.model_predictions.items():
        print(f"  {model}: {pred:.4f}")


def demo_price_response(intelligence):
    """Demonstrate price response curvature."""
    print_section("CONCEPT 11: PRICE RESPONSE CURVATURE")
    
    response = intelligence.price_response
    
    print(f"Curvature: {response.curvature:.6f}")
    print(f"Linearity Score: {response.linearity_score:.2%}")
    print(f"Saturation Point: {response.saturation_point:.2f}")
    print(f"Elasticity (β): {response.elasticity:.3f}")
    print(f"Volume Levels: {len(response.volume_levels)}")


def demo_information_flow(intelligence):
    """Demonstrate information flow speedometer."""
    print_section("CONCEPT 13: INFORMATION FLOW")
    
    flow = intelligence.information_flow
    
    print(f"Discovery Efficiency: {flow.discovery_efficiency:.2%}")
    print(f"Information Share: {flow.information_share:.2%}")
    print(f"Lead-Lag Score: {flow.lead_lag_score:+.3f}")
    print(f"Noise Ratio: {flow.noise_ratio:.2%}")
    print(f"Speed of Adjustment: {flow.speed_of_adjustment:.2%}")
    print(f"Information Asymmetry: {flow.information_asymmetry:.2%}")


def demo_strategy_views(intelligence):
    """Demonstrate strategy-specific views."""
    print_section("CONCEPT 14: STRATEGY-SPECIFIC VIEWS")
    
    views = intelligence.strategy_views
    
    for lens, view in views.items():
        print(f"\n{lens.name} STRATEGY:")
        print(f"  Signal: {view.signal_strength:+.2f}")
        print(f"  Confidence: {view.confidence:.2%}")
        print(f"  Entry Quality: {view.entry_quality:.2%}")
        print(f"  Risk/Reward: {view.risk_reward:.2f}")
        print(f"  Timing: {view.timing_score:.2%}")


def demo_overlays(intelligence):
    """Demonstrate confidence-weighted overlays."""
    print_section("CONCEPT 15: CONFIDENCE-WEIGHTED OVERLAYS")
    
    overlays = intelligence.overlays
    
    print(f"Total Overlays: {len(overlays)}")
    
    for overlay in overlays:
        visible = "✓" if overlay.visible else "✗"
        print(f"\n  [{visible}] {overlay.overlay_type}")
        print(f"      Confidence: {overlay.confidence:.2%}")
        print(f"      Opacity: {overlay.opacity:.2%}")
        print(f"      Z-Index: {overlay.z_index}")


def demo_performance():
    """Demonstrate performance metrics."""
    print_section("PERFORMANCE METRICS")
    
    # Create orchestrator
    orchestrator = MarketIntelligenceOrchestrator()
    
    # Generate more data
    prices, volumes, bids, asks = generate_synthetic_market_data(1000)
    
    # Warm up
    for i in range(100):
        orchestrator.update("BTCUSDT", prices[i], volumes[i], bids[i], asks[i])
    
    # Benchmark
    latencies = []
    for i in range(100, 500):
        start = time.perf_counter()
        orchestrator.update("BTCUSDT", prices[i], volumes[i], bids[i], asks[i])
        latencies.append((time.perf_counter() - start) * 1000)
    
    metrics = orchestrator.get_metrics()
    
    print(f"Updates Processed: {metrics.update_count}")
    print(f"Average Latency: {np.mean(latencies):.2f} ms")
    print(f"P50 Latency: {np.percentile(latencies, 50):.2f} ms")
    print(f"P95 Latency: {np.percentile(latencies, 95):.2f} ms")
    print(f"P99 Latency: {np.percentile(latencies, 99):.2f} ms")
    print(f"Max Latency: {np.max(latencies):.2f} ms")
    print(f"\nLatency Budget: <5ms per symbol")
    print(f"Status: {'✓ PASS' if np.percentile(latencies, 95) < 5 else '✗ FAIL'}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  DEEPCHART MARKET INTELLIGENCE DEMO")
    print("  15 Unified Concepts for Market Structure Understanding")
    print("=" * 60)
    
    # Basic usage
    orchestrator, intelligence = demo_basic_usage()
    
    # Individual concept demos
    demo_friction_map(intelligence)
    demo_regime_detection(intelligence)
    demo_time_to_move(intelligence)
    demo_liquidity(intelligence)
    demo_memory_levels(intelligence)
    demo_execution_quality(intelligence)
    demo_micro_trends(intelligence)
    demo_vacuums(intelligence)
    demo_disagreement(intelligence)
    demo_price_response(intelligence)
    demo_information_flow(intelligence)
    demo_strategy_views(intelligence)
    demo_overlays(intelligence)
    
    # Performance
    demo_performance()
    
    print_section("DEMO COMPLETE")
    print("All 15 market intelligence concepts demonstrated successfully!")
    print("\nFor production use:")
    print("  from trading_bot.deepchart import MarketIntelligenceOrchestrator")
    print("  orchestrator = MarketIntelligenceOrchestrator()")
    print("  intelligence = orchestrator.update(symbol, price, volume, bid, ask)")


if __name__ == "__main__":
    main()
