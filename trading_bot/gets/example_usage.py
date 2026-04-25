"""
GETS Example Usage

Demonstrates how to use the Governed Evolving Time-Series Foundation System.
"""

import logging
from datetime import datetime

from trading_bot.gets import create_gets, GETSConfig
from trading_bot.gets.integration import MarketDataAdapter, create_integrated_gets
from trading_bot.gets.types import ForecastHorizon

logging.basicConfig(level=logging.INFO)


def example_basic_usage():
    """Basic GETS initialization and signal generation."""
    print("=" * 80)
    print("GETS Basic Usage Example")
    print("=" * 80)
    
    # Create GETS with default configuration
    gets = create_gets()
    
    # Initialize the system
    print("\n1. Initializing GETS...")
    success = gets.initialize()
    print(f"   Initialization: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        return
    
    # Create sample market data
    print("\n2. Creating market data...")
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 150.0,
            'high': 152.5,
            'low': 149.5,
            'close': 151.0,
            'volume': 1000000,
            'spread': 0.001,  # 0.1% spread
            'volatility': 0.25  # 25% annualized vol
        },
        symbol="AAPL",
        timestamp=datetime.now()
    )
    print(f"   Symbol: {market_data.symbol}")
    print(f"   Price: ${market_data.ohlcv['close']}")
    
    # Generate signal
    print("\n3. Generating trading signal...")
    signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
    
    print(f"   Direction: {signal.direction} ({'BUY' if signal.direction > 0 else 'SELL' if signal.direction < 0 else 'NEUTRAL'})")
    print(f"   Confidence: {signal.confidence:.2%}")
    print(f"   Expected Edge: {signal.expected_edge:.4f}")
    print(f"   Governance Decision: {signal.governance_decision.name}")
    print(f"   Abstain Recommended: {signal.abstain_recommended}")
    
    if signal.abstain_reason:
        print(f"   Abstain Reason: {signal.abstain_reason}")
    
    # Show disagreement geometry
    print("\n4. Disagreement Geometry:")
    geom = signal.disagreement_geometry
    print(f"   Forecast Consensus: {geom.forecast_consensus_score:.2%}")
    print(f"   Directional Disagreement: {geom.directional_disagreement:.2%}")
    if geom.disagreement_pattern:
        print(f"   Detected Pattern: {geom.disagreement_pattern.name}")
    print(f"   Most Bullish Model: {geom.most_bullish_model.value}")
    print(f"   Most Bearish Model: {geom.most_bearish_model.value}")
    
    # Show diagnosis
    print("\n5. Self-Diagnosis:")
    diag = signal.diagnosis_report
    print(f"   Overall Passed: {diag.overall_passed}")
    print(f"   Stability Passed: {diag.stability_passed}")
    print(f"   Evidence Passed: {diag.evidence_passed}")
    print(f"   Regime Passed: {diag.regime_passed}")
    
    if diag.blocking_issues:
        print(f"   Blocking Issues: {', '.join(diag.blocking_issues[:2])}")
    
    # Record outcome
    print("\n6. Recording outcome...")
    realized_return = 0.015  # Simulated 1.5% return
    gets.record_outcome(signal, realized_return, market_data)
    print(f"   Recorded: predicted={signal.expected_edge:.4f}, realized={realized_return:.4f}")
    
    # Get system status
    print("\n7. System Status:")
    status = gets.get_system_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Shutdown
    print("\n8. Shutting down...")
    gets.shutdown()
    print("   Done.")


def example_with_custom_config():
    """GETS with custom configuration."""
    print("\n" + "=" * 80)
    print("GETS Custom Configuration Example")
    print("=" * 80)
    
    # Create custom configuration
    config = GETSConfig(
        kronos_enabled=True,
        timesfm_enabled=True,
        moirai_enabled=True,
        ttm_enabled=False,  # Disable TTM
        
        # LoRA settings
        lora_rank=16,
        lora_alpha=32.0,
        
        # Diagnosis thresholds
        stability_threshold=0.8,
        evidence_threshold=0.7,
        
        # Governance
        require_human_promotion=True,
        
        # Integration
        decision_governance_integration=True
    )
    
    gets = create_gets(config)
    
    print(f"Configuration:")
    print(f"  LoRA Rank: {config.lora_rank}")
    print(f"  Stability Threshold: {config.stability_threshold}")
    print(f"  Human Promotion Required: {config.require_human_promotion}")
    
    gets.initialize()
    
    print(f"\nFoundation Models Enabled:")
    print(f"  Kronos: {config.kronos_enabled}")
    print(f"  TimesFM: {config.timesfm_enabled}")
    print(f"  Moirai: {config.moirai_enabled}")
    print(f"  TTM: {config.ttm_enabled}")
    
    gets.shutdown()


def example_integration():
    """GETS with full integration (DGS + Trading Bridge)."""
    print("\n" + "=" * 80)
    print("GETS Full Integration Example")
    print("=" * 80)
    
    # Create with full integration
    gets, dgs_adapter, trading_bridge = create_integrated_gets(
        config=None,
        enable_dgs=True,
        enable_trading_bridge=True
    )
    
    gets.initialize()
    
    # Generate signal
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 45000.0,
            'high': 45500.0,
            'low': 44800.0,
            'close': 45200.0,
            'volume': 50000,
            'spread': 0.0005,
            'volatility': 0.65
        },
        symbol="BTC-USD"
    )
    
    signal = gets.generate_signal(market_data, ForecastHorizon.MEDIUM)
    
    print(f"Signal generated for {signal.symbol}")
    print(f"  Expected Edge: {signal.expected_edge:.4f}")
    print(f"  Direction: {signal.direction}")
    
    # Convert to order
    if trading_bridge:
        order = trading_bridge.signal_to_order(
            signal,
            portfolio_value=100000.0,
            current_position=0.0
        )
        
        if order:
            print(f"\nGenerated Order:")
            print(f"  Side: {order['side']}")
            print(f"  Quantity: {order['quantity']:.4f}")
            print(f"  Expected Edge: {order['expected_edge']:.4f}")
            print(f"  Source Models: {', '.join(order['source_models'])}")
        else:
            print("\nNo order generated (signal abstained or edge insufficient)")
    
    # Show DGS status
    if dgs_adapter:
        print(f"\nDGS Integration: {'Active' if dgs_adapter.dgs_available else 'Not Available'}")
    
    gets.shutdown()


def example_evolution_workflow():
    """Demonstrate Layer 4 evolution workflow."""
    print("\n" + "=" * 80)
    print("GETS Evolution Workflow Example")
    print("=" * 80)
    
    gets = create_gets()
    gets.initialize()
    
    # Simulate some failures to trigger evolution
    print("\n1. Simulating failures for pattern analysis...")
    
    for i in range(10):
        market_data = MarketDataAdapter.from_price_dict(
            price_data={
                'open': 100.0,
                'high': 101.0,
                'low': 99.0,
                'close': 100.0 + i * 0.1,
                'volume': 1000000,
                'volatility': 0.15 if i < 5 else 0.45  # Change regime mid-way
            },
            symbol="TEST"
        )
        
        signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
        
        # Simulate poor outcome for some signals
        realized = -0.02 if i % 3 == 0 else 0.01
        gets.record_outcome(signal, realized, market_data)
    
    # Analyze failures
    print("\n2. Analyzing failure patterns...")
    evolution_status = gets.get_evolution_status()
    
    print(f"   Failure Clusters Found: {evolution_status['failure_clusters']}")
    for cluster in evolution_status.get('cluster_details', []):
        print(f"     - {cluster['id']}: {cluster['count']} failures")
    
    # Propose mutations
    print("\n3. Proposing mutations...")
    candidates = gets.layer4_evolution.propose_mutations(gets.config)
    print(f"   Mutation Candidates: {len(candidates)}")
    
    for c in candidates:
        print(f"     - {c.candidate_id}: {c.mutation_type}")
        print(f"       Target: {c.target_model.value}")
        print(f"       Expected: {c.expected_improvement}")
    
    # Show champion status
    print("\n4. Pending Champions:")
    print(f"   Count: {evolution_status['pending_champions']}")
    for c in evolution_status.get('champion_details', []):
        print(f"     - {c['id']}: IC improvement {c['ic_improvement']:.4f}")
    
    gets.shutdown()


def example_multi_horizon():
    """Generate signals across multiple time horizons."""
    print("\n" + "=" * 80)
    print("GETS Multi-Horizon Analysis Example")
    print("=" * 80)
    
    gets = create_gets()
    gets.initialize()
    
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 175.0,
            'high': 176.5,
            'low': 174.5,
            'close': 176.0,
            'volume': 2000000,
            'spread': 0.0008,
            'volatility': 0.20
        },
        symbol="MSFT"
    )
    
    horizons = [
        ("Immediate (1m)", ForecastHorizon.IMMEDIATE),
        ("Short (5m)", ForecastHorizon.SHORT),
        ("Medium (1h)", ForecastHorizon.MEDIUM),
        ("Long (1d)", ForecastHorizon.LONG),
    ]
    
    print(f"\nMulti-horizon analysis for {market_data.symbol}:")
    print(f"Current Price: ${market_data.ohlcv['close']}")
    print("-" * 60)
    
    for name, horizon in horizons:
        signal = gets.generate_signal(market_data, horizon)
        
        print(f"\n{name}:")
        print(f"  Direction: {signal.direction}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Edge: {signal.expected_edge:.4f}")
        print(f"  Decision: {signal.governance_decision.name}")
        print(f"  Prediction Interval: [{signal.uncertainty_quantile_05:.2f}, {signal.uncertainty_quantile_95:.2f}]")
    
    gets.shutdown()


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_with_custom_config()
    example_integration()
    example_evolution_workflow()
    example_multi_horizon()
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)
