"""
Decision Governance System - Example Usage

Demonstrates how to use the complete DGS for trading decisions.
"""

import asyncio
from datetime import datetime
from trading_bot.decision_governance import (
    DecisionGovernanceSystem,
    GovernanceDecision,
    MarketRegime,
    ExecutionFeasibility
)


async def main():
    """Main example demonstrating DGS usage"""
    
    # Initialize the governance system
    print("Initializing Decision Governance System...")
    dgs = DecisionGovernanceSystem(
        storage_path="./dgs_example_data",
        realtime_latency_ms=100
    )
    
    await dgs.start()
    print("DGS started successfully\n")
    
    # Example 1: Evaluate a buy signal
    print("=" * 60)
    print("Example 1: Evaluating BUY signal for AAPL")
    print("=" * 60)
    
    # Create a trading signal
    buy_signal = {
        'source': 'trend_following_agent',
        'direction': 'buy',
        'confidence': 0.75,
        'size': 1.0,
        'rationale': 'Strong uptrend with volume confirmation',
        'timeframe': '1d',
        'assumptions': [
            'Trend will continue',
            'No major earnings surprise'
        ],
        'evidence': [
            'Price above 50-day MA',
            'Volume 2x average',
            'RSI at 60 (not overbought)'
        ]
    }
    
    # Define current market regime
    current_regime = MarketRegime(
        volatility_state="normal",
        liquidity_state="ample",
        trend_persistence=0.7,
        correlation_clustering="dispersed",
        macro_event_density="quiet",
        order_flow_toxicity="benign",
        spread_impact_conditions="favorable"
    )
    
    # Define execution feasibility
    execution = ExecutionFeasibility(
        feasible=True,
        expected_slippage=0.001,
        expected_fill_rate=0.95,
        cost_adjusted_expectancy=0.02,
        liquidity_score=0.8
    )
    
    # Evaluate signal through governance
    decision, record = await dgs.evaluate_trade_signal(
        signal=buy_signal,
        symbol='AAPL',
        current_regime=current_regime,
        execution_feasibility=execution,
        hard_constraints={
            'max_position_size': 0.1,
            'daily_loss_limit': 0.02,
            'max_positions': 10,
            'current_positions': 5
        }
    )
    
    print(f"Decision: {decision.value.upper()}")
    print(f"Decision ID: {record.id}")
    print(f"Confidence: {record.uncertainty_profile.overall_confidence:.2f}")
    print(f"Robustness: {record.robustness_score:.2f}")
    print(f"Regime Fit: {record.regime_applicability_score:.2f}")
    print(f"Reasoning: {record.decision_reasoning[:100]}...")
    print()
    
    # If approved, record outcome
    if decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
        print("Trade executed. Recording outcome...")
        
        # Simulate trade outcome (positive)
        await dgs.record_trade_outcome(
            decision_id=record.id,
            pnl=0.035,  # 3.5% profit
            slippage=0.001,
            fill_behavior="full",
            invalidation_hit=False,
            expected_pnl=0.02
        )
        print("Outcome recorded: +3.5% PnL\n")
    
    # Example 2: Evaluate a risky signal
    print("=" * 60)
    print("Example 2: Evaluating RISKY signal for TSLA")
    print("=" * 60)
    
    risky_signal = {
        'source': 'momentum_agent',
        'direction': 'buy',
        'confidence': 0.85,  # High confidence
        'size': 2.0,  # Large position
        'rationale': 'Breaking out on high volume',
        'timeframe': '1d',
        'evidence': [
            'New 52-week high'
        ]  # Limited evidence
    }
    
    # Risky regime
    risky_regime = MarketRegime(
        volatility_state="extreme",
        liquidity_state="constrained",
        trend_persistence=0.3,  # Low persistence
        correlation_clustering="high",
        macro_event_density="elevated",
        order_flow_toxicity="toxic",
        spread_impact_conditions="adverse"
    )
    
    decision2, record2 = await dgs.evaluate_trade_signal(
        signal=risky_signal,
        symbol='TSLA',
        current_regime=risky_regime,
        execution_feasibility=execution,
        hard_constraints={
            'max_position_size': 0.1,
            'daily_loss_limit': 0.02,
            'max_positions': 10,
            'current_positions': 5
        }
    )
    
    print(f"Decision: {decision2.value.upper()}")
    print(f"Decision ID: {record2.id}")
    print(f"Confidence: {record2.uncertainty_profile.overall_confidence:.2f}")
    print(f"Reasoning: {record2.decision_reasoning[:100]}...")
    
    if decision2 in [GovernanceDecision.REJECT, GovernanceDecision.ABSTAIN]:
        print("Trade blocked by governance system.")
        print(f"Abstention probability: {record2.uncertainty_profile.abstention_probability:.2f}")
    print()
    
    # Example 3: Run offline analysis
    print("=" * 60)
    print("Example 3: Running Offline Analysis")
    print("=" * 60)
    
    analysis_results = await dgs.run_offline_analysis()
    
    print(f"Analysis completed at: {analysis_results['analysis_timestamp']}")
    print(f"Sections analyzed: {list(analysis_results['sections'].keys())}")
    
    if 'failure_patterns' in analysis_results['sections']:
        fp = analysis_results['sections']['failure_patterns']
        print(f"Total patterns: {fp['total_patterns']}")
        print(f"Top patterns: {[p['name'] for p in fp['top_patterns'][:3]]}")
    print()
    
    # Example 4: Run capability discovery
    print("=" * 60)
    print("Example 4: Running Capability Discovery")
    print("=" * 60)
    
    discovery_results = await dgs.run_capability_discovery()
    
    print(f"Observations tracked: {discovery_results['steps']['observation']['observations_count']}")
    print(f"Limitations detected: {discovery_results['steps']['limitation_detection']['limitations_detected']}")
    print(f"Hypotheses generated: {discovery_results['steps']['hypothesis_generation']['hypotheses_generated']}")
    print()
    
    # Get system status
    print("=" * 60)
    print("System Status")
    print("=" * 60)
    
    status = dgs.get_system_status()
    
    print(f"System running: {status['running']}")
    print(f"Real-time decisions: {status['realtime_plane']['total_decisions']}")
    print(f"Decision distribution: {status['realtime_plane']['decision_distribution']}")
    print(f"Failure patterns: {status['memory_systems']['failure_patterns']['total_patterns']}")
    print()
    
    # Generate comprehensive report
    print("=" * 60)
    print("Comprehensive Report Summary")
    print("=" * 60)
    
    report = dgs.generate_comprehensive_report()
    
    print(f"Decision approval rate: {report['decision_statistics'].get('approval_rate', 0):.2%}")
    print(f"Calibration Brier score: {report['calibration_metrics'].get('average_brier_score', 0.25):.3f}")
    print(f"Capability gaps identified: {len(report['capability_gaps'])}")
    print()
    
    # Stop the system
    await dgs.stop()
    print("DGS stopped. Example complete.")


if __name__ == "__main__":
    asyncio.run(main())
