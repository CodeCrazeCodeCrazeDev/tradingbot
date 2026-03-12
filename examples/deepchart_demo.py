"""
DeepChart Demo - Low-Cost Deep Learning Visualization Layer

This demo showcases the complete DeepChart system:
1. Feature extraction from L1 data
2. Lightweight ML inference
3. Visualization generation
4. Self-improvement monitoring

Run: python examples/deepchart_demo.py
"""

import sys
import os
import time
import json
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.deepchart import (
    DeepChartOrchestrator,
    OrchestratorConfig,
    DeepChartFeatureEngine,
    FeatureConfig,
    DeepChartModel,
    ModelConfig,
    InferenceEngine,
    InferenceConfig,
    DeepChartVisualizer,
    VisualizationConfig,
)


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_feature_extraction():
    """Demonstrate feature extraction from L1 data."""
    print_header("FEATURE EXTRACTION DEMO")
    
    # Create feature engine
    config = FeatureConfig(
        short_window=20,
        medium_window=100,
        long_window=500,
    )
    engine = DeepChartFeatureEngine(config)
    
    # Simulate L1 data
    np.random.seed(42)
    price = 100.0
    
    print("\nSimulating 200 bars of L1 data...")
    
    for i in range(200):
        # Random walk with trend
        trend = 0.01 if i < 100 else -0.01
        price += np.random.randn() * 0.5 + trend
        volume = np.random.exponential(1000)
        spread = 0.05 + np.random.exponential(0.02)
        
        features = engine.update(
            price=price,
            volume=volume,
            bid=price - spread / 2,
            ask=price + spread / 2,
            timestamp=time.time() + i,
        )
        
        if i % 50 == 0 and features['initialized']:
            micro = features['microstructure']
            regime = features['regime']
            liquidity = features['liquidity']
            latent = features['latent']
            
            print(f"\n--- Bar {i} ---")
            print(f"Price: {price:.2f}")
            print(f"\nMicrostructure Features:")
            print(f"  Trade Imbalance: {micro.trade_imbalance:+.3f}")
            print(f"  Volume Imbalance: {micro.volume_imbalance:+.3f}")
            print(f"  Spread (bps): {micro.spread_bps:.1f}")
            print(f"  Friction: {micro.friction_coefficient:.4f}")
            print(f"  Burst Indicator: {micro.burst_indicator:.3f}")
            
            print(f"\nRegime Features:")
            print(f"  Regime: {['Trending', 'Ranging', 'Volatile', 'Quiet'][regime.regime_id]}")
            print(f"  Confidence: {regime.regime_confidence:.2f}")
            print(f"  Trend Strength: {regime.trend_strength:+.3f}")
            print(f"  Vol Compression: {regime.vol_compression:.3f}")
            
            print(f"\nLiquidity Features:")
            print(f"  Liquidity Score: {liquidity.liquidity_score:.3f}")
            print(f"  Depth Imbalance: {liquidity.depth_imbalance:+.3f}")
            print(f"  Thin Market: {liquidity.thin_market_alert}")
            
            print(f"\nLatent Features:")
            print(f"  Breakout Prob: {latent.breakout_probability:.3f}")
            print(f"  Reversion Prob: {latent.reversion_probability:.3f}")
            print(f"  Micro Momentum: {latent.micro_momentum:+.4f}")
    
    # Get feature vector
    vector = engine.get_feature_vector()
    print(f"\n\nFeature Vector Shape: {vector.shape}")
    print(f"Feature Vector (first 10): {vector[:10]}")


def demo_model_inference():
    """Demonstrate lightweight model inference."""
    print_header("MODEL INFERENCE DEMO")
    
    # Create model
    config = ModelConfig(
        input_dim=32,
        sequence_length=64,
        hidden_dim=64,
        latent_dim=8,
    )
    model = DeepChartModel(config)
    
    print(f"\nModel Info:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Simulate inference
    print("\nRunning inference on simulated data...")
    
    np.random.seed(42)
    latencies = []
    
    for i in range(100):
        # Generate random feature vector
        feature_vector = np.random.randn(config.input_dim).astype(np.float32)
        
        # Run inference
        output = model.predict(feature_vector)
        latencies.append(output.inference_time_ms)
        
        if i % 25 == 0:
            print(f"\n--- Inference {i} ---")
            print(f"  Trend: {output.trend_direction} (conf: {output.trend_confidence:.2f})")
            print(f"  Vol Regime: {output.volatility_regime} (score: {output.volatility_score:.2f})")
            print(f"  Breakout Prob: {output.breakout_probability:.3f}")
            print(f"  Reversion Prob: {output.reversion_probability:.3f}")
            print(f"  Regime: {output.regime_id} (probs: {[f'{p:.2f}' for p in output.regime_probs]})")
            print(f"  Latent State: {[f'{x:.2f}' for x in output.latent_state[:4]]}...")
            print(f"  Inference Time: {output.inference_time_ms:.2f}ms")
    
    print(f"\n\nLatency Statistics:")
    print(f"  Mean: {np.mean(latencies):.2f}ms")
    print(f"  Std: {np.std(latencies):.2f}ms")
    print(f"  Max: {np.max(latencies):.2f}ms")
    print(f"  Min: {np.min(latencies):.2f}ms")


def demo_inference_engine():
    """Demonstrate real-time inference engine."""
    print_header("INFERENCE ENGINE DEMO")
    
    # Create inference engine
    config = InferenceConfig(
        inference_interval_ms=50,
        max_inference_latency_ms=5.0,
        cache_ttl_ms=200,
    )
    engine = InferenceEngine(config)
    
    # Add symbols
    engine.add_symbol("BTCUSDT")
    engine.add_symbol("ETHUSDT")
    
    print("\nTracking symbols: BTCUSDT, ETHUSDT")
    
    # Simulate market data
    np.random.seed(42)
    btc_price = 50000.0
    eth_price = 3000.0
    
    print("\nSimulating 200 updates...")
    
    for i in range(200):
        # Random walk
        btc_price += np.random.randn() * 50
        eth_price += np.random.randn() * 5
        
        # Update
        btc_result = engine.update(
            symbol="BTCUSDT",
            price=btc_price,
            volume=np.random.exponential(100),
            bid=btc_price - 5,
            ask=btc_price + 5,
        )
        
        eth_result = engine.update(
            symbol="ETHUSDT",
            price=eth_price,
            volume=np.random.exponential(500),
            bid=eth_price - 0.5,
            ask=eth_price + 0.5,
        )
        
        if i % 50 == 0:
            print(f"\n--- Update {i} ---")
            if btc_result:
                print(f"BTC: trend={btc_result.model_output.trend_direction}, "
                      f"breakout={btc_result.model_output.breakout_probability:.3f}, "
                      f"from_cache={btc_result.from_cache}")
            if eth_result:
                print(f"ETH: trend={eth_result.model_output.trend_direction}, "
                      f"breakout={eth_result.model_output.breakout_probability:.3f}, "
                      f"from_cache={eth_result.from_cache}")
    
    # Print metrics
    print("\n\nEngine Metrics:")
    metrics = engine.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")


def demo_visualization():
    """Demonstrate visualization layer."""
    print_header("VISUALIZATION DEMO")
    
    # Create visualizer
    config = VisualizationConfig(
        width=1200,
        height=600,
        show_latent_zones=True,
        show_support_resistance=True,
        show_momentum_arrows=True,
    )
    visualizer = DeepChartVisualizer(config)
    
    # Simulate data with mock inference results
    np.random.seed(42)
    price = 100.0
    
    print("\nGenerating visualization data...")
    
    # Create mock ModelOutput class for demo
    class MockModelOutput:
        def __init__(self):
            self.regime_id = np.random.randint(0, 4)
            self.prediction_confidence = 0.5 + np.random.random() * 0.5
            self.latent_state = np.random.randn(8)
            self.volatility_score = np.random.random()
    
    class MockInferenceResult:
        def __init__(self):
            self.model_output = MockModelOutput()
            self.signals = {'momentum_signal': np.random.randn() * 0.2}
    
    for i in range(200):
        price += np.random.randn() * 0.5
        volume = np.random.exponential(1000)
        
        mock_result = MockInferenceResult()
        visualizer.update(price, volume, mock_result)
    
    # Update levels
    visualizer.update_levels(
        support_levels=np.array([95.0, 90.0, 85.0]),
        resistance_levels=np.array([105.0, 110.0, 115.0]),
        bid_depth=np.random.random(5),
        ask_depth=np.random.random(5),
    )
    
    # Generate outputs
    print("\n1. JSON Output:")
    json_output = visualizer.to_json()
    print(f"   Keys: {list(json_output.keys())}")
    print(f"   Overlays: {len(json_output['overlays'])}")
    print(f"   Data points: {len(json_output['priceData']['prices'])}")
    
    print("\n2. WebGL Data:")
    webgl_data = visualizer.to_webgl_data()
    print(f"   Vertices: {list(webgl_data['vertices'].keys())}")
    print(f"   Uniforms: {webgl_data['uniforms']}")
    
    print("\n3. SVG Output:")
    svg = visualizer.to_svg_paths()
    print(f"   SVG length: {len(svg)} characters")
    print(f"   Preview: {svg[:200]}...")
    
    # Print overlay details
    print("\n4. Overlay Details:")
    for overlay in json_output['overlays']:
        print(f"   - {overlay['type']}: z={overlay['zIndex']}, visible={overlay['visible']}")


def demo_full_orchestrator():
    """Demonstrate full orchestrator."""
    print_header("FULL ORCHESTRATOR DEMO")
    
    # Create orchestrator
    config = OrchestratorConfig(
        enable_visualization=True,
        enable_self_improvement=True,
        enable_api=True,
        collect_training_data=False,  # Disable for demo
    )
    orchestrator = DeepChartOrchestrator(config)
    
    # Add symbols
    orchestrator.add_symbol("BTCUSDT")
    orchestrator.add_symbol("ETHUSDT")
    orchestrator.add_symbol("SOLUSDT")
    
    print("\nTracking: BTCUSDT, ETHUSDT, SOLUSDT")
    
    # Simulate market data
    np.random.seed(42)
    prices = {
        "BTCUSDT": 50000.0,
        "ETHUSDT": 3000.0,
        "SOLUSDT": 100.0,
    }
    
    print("\nRunning simulation...")
    
    for i in range(200):
        for symbol in prices:
            # Random walk
            volatility = {"BTCUSDT": 50, "ETHUSDT": 5, "SOLUSDT": 1}[symbol]
            prices[symbol] += np.random.randn() * volatility
            
            # Update
            result = orchestrator.update(
                symbol=symbol,
                price=prices[symbol],
                volume=np.random.exponential(100),
                bid=prices[symbol] * 0.9999,
                ask=prices[symbol] * 1.0001,
            )
        
        if i % 50 == 0:
            print(f"\n--- Step {i} ---")
            
            # Get predictions via API
            for symbol in prices:
                pred = orchestrator.get_prediction(symbol)
                if pred and 'model_output' in pred:
                    mo = pred['model_output']
                    print(f"{symbol}: trend={mo['trend_direction']}, "
                          f"breakout={mo['breakout_probability']:.3f}")
    
    # Get system status
    print("\n\nSystem Status:")
    status = orchestrator.get_status()
    print(f"  Symbols: {status['symbols']}")
    print(f"  Inference metrics:")
    for key, value in status['inference_metrics'].items():
        print(f"    {key}: {value}")
    
    # Get visualization for one symbol
    print("\n\nVisualization (BTCUSDT):")
    viz = orchestrator.get_visualization("BTCUSDT")
    if viz:
        print(f"  Overlays: {len(viz['overlays'])}")
        print(f"  Data points: {len(viz['priceData']['prices'])}")
    
    # Shutdown
    orchestrator.shutdown()
    print("\nOrchestrator shutdown complete.")


def demo_performance_budget():
    """Display performance budget."""
    print_header("PERFORMANCE BUDGET")
    
    budget = """
    INFERENCE LATENCY (per symbol):
    ├── Target: <5ms
    ├── Max acceptable: 10ms
    └── Degraded mode: <2ms

    STORAGE COST (per day, per symbol):
    ├── Feature history: ~2MB
    ├── Training data: ~10MB (if collecting)
    ├── Model files: ~5MB
    └── Total: <20MB/day/symbol

    RAM USAGE:
    ├── Per symbol state: ~500KB
    ├── Model in memory: ~10MB (shared)
    ├── Inference buffers: ~1MB
    └── Total (50 symbols): <100MB

    CLIENT RENDERING:
    ├── WebGL draw calls: <100/frame
    ├── Texture memory: <50MB
    ├── Frame time: <16ms (60fps)
    └── Overlay computation: <5ms

    MODEL CONSTRAINTS:
    ├── Total parameters: <1M
    ├── Model file size: <10MB
    ├── ONNX compatible: Required
    └── GPU required: No

    COST ESTIMATE (50 symbols):
    ├── Compute: $0 (CPU only)
    ├── Storage: ~$1/month
    ├── Data feeds: $0-50/month
    └── Total: <$50/month
    """
    print(budget)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  DeepChart - Low-Cost Deep Learning Visualization Layer")
    print("  Demo Script")
    print("=" * 60)
    
    demos = [
        ("Feature Extraction", demo_feature_extraction),
        ("Model Inference", demo_model_inference),
        ("Inference Engine", demo_inference_engine),
        ("Visualization", demo_visualization),
        ("Full Orchestrator", demo_full_orchestrator),
        ("Performance Budget", demo_performance_budget),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run all demos")
    print(f"  0. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (0-7): ").strip()
            
            if choice == "0":
                print("Exiting...")
                break
            elif choice == str(len(demos) + 1):
                for name, func in demos:
                    func()
                break
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(demos):
                    demos[idx][1]()
                else:
                    print("Invalid choice")
        except ValueError:
            print("Please enter a number")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
