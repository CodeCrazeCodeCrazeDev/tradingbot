"""
GETS Demonstration Script

Shows the complete Governed Evolving Time-Series Foundation System in action.
Demonstrates all 5 layers and multi-modal awareness.
"""

import logging
import numpy as np
from datetime import datetime, timedelta

from trading_bot.gets import create_gets, GETSConfig
from trading_bot.gets.integration import MarketDataAdapter, create_integrated_gets
from trading_bot.gets.types import ForecastHorizon, MarketData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_basic_signal_generation():
    """Demonstrate basic signal generation through all 5 layers."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Signal Generation (All 5 Layers)")
    print("=" * 80)
    
    # Create GETS
    gets = create_gets()
    success = gets.initialize()
    
    if not success:
        print("ERROR: Failed to initialize GETS")
        return
    
    # Create market data for AAPL
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 150.0,
            'high': 152.5,
            'low': 149.5,
            'close': 151.0,
            'volume': 1000000,
            'spread': 0.001,
            'volatility': 0.25
        },
        symbol="AAPL",
        timestamp=datetime.now()
    )
    
    print(f"\nInput Market Data:")
    print(f"  Symbol: {market_data.symbol}")
    print(f"  Price: ${market_data.ohlcv['close']}")
    print(f"  Spread: {market_data.bid_ask_spread}")
    print(f"  Volatility: {market_data.realized_volatility}")
    
    # Generate signal through all layers
    print(f"\n--- Layer 1: Temporal Perception ---")
    print(f"  Foundation models generating forecasts...")
    
    print(f"\n--- Layer 2: Forecast & Representation ---")
    print(f"  Trading-native heads computing edge-after-cost...")
    
    print(f"\n--- Layer 3: Self-Diagnosis ---")
    print(f"  Introspection engine validating forecast stability...")
    print(f"  Computing disagreement geometry...")
    
    signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
    
    print(f"\n--- Layer 5: Governance Decision ---")
    print(f"\nOUTPUT SIGNAL:")
    print(f"  Direction: {signal.direction} ({'BUY' if signal.direction > 0 else 'SELL' if signal.direction < 0 else 'NEUTRAL'})")
    print(f"  Confidence: {signal.confidence:.2%}")
    print(f"  Expected Edge: {signal.expected_edge:.4f} ({signal.expected_edge*10000:.1f} bps)")
    print(f"  Governance Decision: {signal.governance_decision.name}")
    print(f"  Abstain Recommended: {signal.abstain_recommended}")
    
    if signal.abstain_reason:
        print(f"  Abstain Reason: {signal.abstain_reason}")
    
    # Show disagreement geometry
    print(f"\nDISAGREEMENT GEOMETRY (Layer 3 Output):")
    geom = signal.disagreement_geometry
    print(f"  Forecast Consensus: {geom.forecast_consensus_score:.2%}")
    print(f"  Directional Disagreement: {geom.directional_disagreement:.2%}")
    print(f"  Cross-Model Stability: {geom.cross_model_stability:.2%}")
    print(f"  Disagreement Entropy: {geom.disagreement_entropy:.2%}")
    
    if geom.disagreement_pattern:
        print(f"  Detected Pattern: {geom.disagreement_pattern.name}")
    
    print(f"  Model Authority Weights:")
    for model, weight in geom.model_authority_weights.items():
        print(f"    {model.value}: {weight:.2%}")
    
    # Show diagnosis
    print(f"\nDIAGNOSIS REPORT:")
    diag = signal.diagnosis_report
    print(f"  Stability Passed: {diag.stability_passed}")
    print(f"  Evidence Passed: {diag.evidence_passed}")
    print(f"  Regime Passed: {diag.regime_passed}")
    print(f"  Execution Feasible: {diag.execution_feasible}")
    print(f"  Overall Passed: {diag.overall_passed}")
    
    if diag.blocking_issues:
        print(f"  Blocking Issues: {', '.join(diag.blocking_issues)}")
    
    if diag.warnings:
        print(f"  Warnings: {len(diag.warnings)}")
    
    gets.shutdown()
    print("\n✓ Demo 1 Complete")


def demo_multimodal_awareness():
    """Demonstrate multi-modal awareness components."""
    print("\n" + "=" * 80)
    print("DEMO 2: Multi-Modal Awareness")
    print("=" * 80)
    
    gets = create_gets()
    gets.initialize()
    
    # Create market data with rich features
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 45000.0,
            'high': 46500.0,
            'low': 44800.0,
            'close': 45200.0,
            'volume': 50000,
            'spread': 0.0005,
            'volatility': 0.65,
            'depth_imbalance': 0.3  # More bids than asks
        },
        symbol="BTC-USD"
    )
    
    print(f"\nAnalyzing {market_data.symbol}...")
    
    # Generate signal
    signal = gets.generate_signal(market_data, ForecastHorizon.MEDIUM)
    
    # Run multi-modal awareness analysis
    print(f"\n--- Multi-Modal Awareness Analysis ---")
    
    if gets.awareness:
        awareness_results = gets.awareness.analyze(
            signal=signal,
            market_data=market_data,
            current_positions={},
            portfolio_value=100000.0
        )
        
        # Market Structure
        if "market_structure" in awareness_results:
            mss = awareness_results["market_structure"]
            print(f"\n  Market Structure:")
            print(f"    Spread: {mss.bid_ask_spread_bps:.2f} bps")
            print(f"    Depth Imbalance: {mss.depth_imbalance:.2f}")
            print(f"    Flow Toxicity: {mss.flow_toxicity_score:.2%}")
            print(f"    Est. Slippage: {mss.estimated_slippage_bps:.2f} bps")
            print(f"    Depth Resilience: {mss.depth_resilience_score:.2%}")
        
        # Decision Context
        if "decision" in awareness_results:
            dec = awareness_results["decision"]
            print(f"\n  Decision Awareness:")
            print(f"    Tradable: {dec.forecast_tradable}")
            print(f"    Edge After Cost: {dec.edge_after_cost*10000:.2f} bps")
            print(f"    Cost Estimate: {dec.cost_estimate_bps:.2f} bps")
            print(f"    Tradability Score: {dec.tradability_score:.2%}")
            print(f"    Estimated Capacity: ${dec.estimated_capacity:,.0f}")
        
        # Risk State
        if "risk" in awareness_results:
            risk = awareness_results["risk"]
            print(f"\n  Risk Awareness:")
            print(f"    Drawdown Prob (5%): {risk.drawdown_prob_5pct:.2%}")
            print(f"    VaR 95%: ${risk.var_95:,.0f}")
            print(f"    Recommended Position: {risk.recommended_position_pct:.2%}")
            print(f"    Tail Risk Score: {risk.tail_risk_score:.2%}")
    
    gets.shutdown()
    print("\n✓ Demo 2 Complete")


def demo_evolution_workflow():
    """Demonstrate Layer 4 evolution workflow."""
    print("\n" + "=" * 80)
    print("DEMO 3: Controlled Evolution Workflow (Layer 4)")
    print("=" * 80)
    
    gets = create_gets()
    gets.initialize()
    
    print("\nSimulating 20 trading scenarios with outcomes...")
    
    np.random.seed(42)
    
    for i in range(20):
        # Vary market conditions
        vol = 0.15 if i < 10 else 0.45  # Shift regime mid-way
        spread = 0.001 if i < 15 else 0.003  # Liquidity deterioration
        
        market_data = MarketDataAdapter.from_price_dict(
            price_data={
                'open': 100.0,
                'high': 101.0 + np.random.normal(0, vol/10),
                'low': 99.0 - np.random.normal(0, vol/10),
                'close': 100.0 + np.random.normal(0, vol/5),
                'volume': 1000000 * (1 + np.random.normal(0, 0.1)),
                'spread': spread,
                'volatility': vol
            },
            symbol="TEST_SYMBOL"
        )
        
        signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
        
        # Simulate realized return (sometimes wrong to create failures)
        if i % 4 == 0:  # 25% failure rate
            realized = -signal.expected_edge * 2  # Opposite direction, magnified
        else:
            realized = signal.expected_edge * (0.8 + np.random.normal(0, 0.2))
        
        gets.record_outcome(signal, realized, market_data)
    
    print(f"\n--- Layer 4: Failure Analysis ---")
    evolution_status = gets.get_evolution_status()
    
    print(f"Failure Clusters Detected: {evolution_status['failure_clusters']}")
    
    for cluster in evolution_status.get('cluster_details', []):
        print(f"\n  Cluster: {cluster['id']}")
        print(f"    Failures: {cluster['count']}")
        print(f"    Models: {', '.join(cluster['models'])}")
        print(f"    Regimes: {', '.join(cluster['regimes'])}")
    
    print(f"\n--- Layer 4: Mutation Proposals ---")
    candidates = gets.layer4_evolution.propose_mutations(gets.config)
    print(f"Proposed Mutations: {len(candidates)}")
    
    for c in candidates:
        print(f"\n  Mutation: {c.candidate_id}")
        print(f"    Type: {c.mutation_type}")
        print(f"    Target: {c.target_model.value}")
        print(f"    Expected: {c.expected_improvement}")
        print(f"    Rationale: {c.rationale}")
    
    print(f"\n--- Layer 5: Pending Champions ---")
    print(f"Champions awaiting promotion: {evolution_status['pending_champions']}")
    
    for champ in evolution_status.get('champion_details', []):
        print(f"\n  Champion: {champ['id']}")
        print(f"    IC Improvement: {champ['ic_improvement']:.4f}")
        print(f"    Regime Coverage: {champ['regime_coverage']:.1%}")
        print(f"    Status: Awaiting Layer 5 governance approval")
    
    gets.shutdown()
    print("\n✓ Demo 3 Complete")


def demo_disagreement_patterns():
    """Demonstrate various disagreement patterns."""
    print("\n" + "=" * 80)
    print("DEMO 4: Disagreement Pattern Detection")
    print("=" * 80)
    
    gets = create_gets()
    gets.initialize()
    
    patterns = [
        ("Normal Market", {'close': 150.0, 'volatility': 0.20, 'spread': 0.001}),
        ("High Volatility", {'close': 150.0, 'volatility': 0.60, 'spread': 0.003}),
        ("Low Volatility", {'close': 150.0, 'volatility': 0.08, 'spread': 0.0005}),
        ("Wide Spread", {'close': 150.0, 'volatility': 0.25, 'spread': 0.005}),
    ]
    
    for scenario_name, params in patterns:
        market_data = MarketDataAdapter.from_price_dict(
            price_data={
                'open': params['close'] * 0.99,
                'high': params['close'] * 1.02,
                'low': params['close'] * 0.98,
                'close': params['close'],
                'volume': 1000000,
                'spread': params['spread'],
                'volatility': params['volatility']
            },
            symbol="PATTERN_TEST"
        )
        
        signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
        geom = signal.disagreement_geometry
        
        print(f"\n  {scenario_name}:")
        print(f"    Pattern: {geom.disagreement_pattern.name if geom.disagreement_pattern else 'None'}")
        print(f"    Consensus: {geom.forecast_consensus_score:.2%}")
        print(f"    Stability: {geom.cross_model_stability:.2%}")
        print(f"    Decision: {signal.governance_decision.name}")
    
    gets.shutdown()
    print("\n✓ Demo 4 Complete")


def demo_multi_horizon():
    """Demonstrate multi-horizon forecasting."""
    print("\n" + "=" * 80)
    print("DEMO 5: Multi-Horizon Forecast Fusion")
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
    
    print(f"\nMulti-horizon analysis for {market_data.symbol} @ ${market_data.ohlcv['close']}")
    print("-" * 60)
    
    for name, horizon in horizons:
        signal = gets.generate_signal(market_data, horizon)
        
        print(f"\n{name}:")
        print(f"  Direction: {signal.direction}")
        print(f"  Edge: {signal.expected_edge*10000:.1f} bps")
        print(f"  Confidence: {signal.confidence:.1%}")
        print(f"  Prediction Range: [{signal.uncertainty_quantile_05:.2f}, {signal.uncertainty_quantile_95:.2f}]")
        print(f"  Decision: {signal.governance_decision.name}")
        print(f"  Models Used: {len(signal.source_models)}")
    
    gets.shutdown()
    print("\n✓ Demo 5 Complete")


def demo_integration():
    """Demonstrate DGS and Trading Bridge integration."""
    print("\n" + "=" * 80)
    print("DEMO 6: Full Integration (DGS + Trading Bridge)")
    print("=" * 80)
    
    gets, dgs_adapter, trading_bridge = create_integrated_gets(
        enable_dgs=True,
        enable_trading_bridge=True
    )
    
    gets.initialize()
    
    market_data = MarketDataAdapter.from_price_dict(
        price_data={
            'open': 3000.0,
            'high': 3050.0,
            'low': 2980.0,
            'close': 3025.0,
            'volume': 25000,
            'spread': 0.0003,
            'volatility': 0.45
        },
        symbol="ETH-USD"
    )
    
    signal = gets.generate_signal(market_data, ForecastHorizon.SHORT)
    
    print(f"\nGETS Signal Generated:")
    print(f"  Symbol: {signal.symbol}")
    print(f"  Direction: {signal.direction}")
    print(f"  Edge: {signal.expected_edge*10000:.2f} bps")
    
    # Trading Bridge
    if trading_bridge:
        order = trading_bridge.signal_to_order(
            signal,
            portfolio_value=100000.0,
            current_position=0.0
        )
        
        if order:
            print(f"\nTrading Bridge - Order Generated:")
            print(f"  Side: {order['side'].upper()}")
            print(f"  Quantity: {order['quantity']:.4f}")
            print(f"  Expected Edge: {order['expected_edge']*10000:.2f} bps")
            print(f"  Source Models: {', '.join(order['source_models'])}")
            print(f"  Timestamp: {order['timestamp']}")
        else:
            print(f"\nTrading Bridge: No order (abstained)")
            if signal.abstain_reason:
                print(f"  Reason: {signal.abstain_reason}")
    
    # DGS Status
    if dgs_adapter:
        status = "ACTIVE" if dgs_adapter.dgs_available else "NOT AVAILABLE"
        print(f"\nDGS Integration: {status}")
    
    gets.shutdown()
    print("\n✓ Demo 6 Complete")


def run_all_demos():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("GETS: GOVERNED EVOLVING TIME-SERIES FOUNDATION SYSTEM")
    print("Complete Demonstration Suite")
    print("=" * 80)
    
    demos = [
        demo_basic_signal_generation,
        demo_multimodal_awareness,
        demo_evolution_workflow,
        demo_disagreement_patterns,
        demo_multi_horizon,
        demo_integration
    ]
    
    for i, demo in enumerate(demos, 1):
        try:
            demo()
        except Exception as e:
            print(f"\n✗ Demo {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. GETS extracts edge from DISAGREEMENT, not prediction alone")
    print("  2. All 5 layers work in sequence with hard governance boundaries")
    print("  3. Multi-modal awareness provides holistic market understanding")
    print("  4. Evolution is sandbox-only with champion-challenger validation")
    print("  5. The system knows when it doesn't know (abstains appropriately)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_all_demos()
