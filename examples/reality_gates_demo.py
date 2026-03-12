"""
Reality Gates Demo - Preventing AI Stupidity in Live Trading

This demo shows how the reality gates protect against common AI trading failures.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.reality_gates import (
    MasterRealityGate,
    DataIntegrityGate,
    WalkForwardGate,
    ExecutionRealismGate,
    MultipleTestingGate,
    DriftDetectionGate,
    KillSwitchGate,
    create_reality_gate,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_data_integrity():
    """Demo: Data Integrity Gate"""
    print_header("DATA INTEGRITY GATE")
    
    gate = DataIntegrityGate()
    
    # Good data
    good_data = {
        'symbol': 'EURUSD',
        'open': 1.0850,
        'high': 1.0875,
        'low': 1.0840,
        'close': 1.0860,
        'volume': 1500000,
        'timestamp': datetime.utcnow()
    }
    
    result = gate.validate(good_data, 'ohlcv')
    print(f"\n[GOOD DATA]")
    print(f"  Score: {result.score:.2f}")
    print(f"  Usable: {result.is_usable}")
    print(f"  Anomalies: {len(result.anomalies)}")
    
    # Bad data - missing values
    bad_data_missing = {
        'symbol': 'EURUSD',
        'open': 1.0850,
        'high': None,  # Missing!
        'low': 1.0840,
        'close': 1.0860,
        'volume': 1500000,
        'timestamp': datetime.utcnow()
    }
    
    result = gate.validate(bad_data_missing, 'ohlcv')
    print(f"\n[MISSING DATA]")
    print(f"  Score: {result.score:.2f}")
    print(f"  Usable: {result.is_usable}")
    print(f"  Anomalies: {[str(a) for a in result.anomalies]}")
    
    # Bad data - impossible values
    bad_data_impossible = {
        'symbol': 'EURUSD',
        'open': 1.0850,
        'high': 1.0830,  # High < Low!
        'low': 1.0870,
        'close': 1.0860,
        'volume': 1500000,
        'timestamp': datetime.utcnow()
    }
    
    result = gate.validate(bad_data_impossible, 'ohlcv')
    print(f"\n[IMPOSSIBLE VALUES]")
    print(f"  Score: {result.score:.2f}")
    print(f"  Usable: {result.is_usable}")
    print(f"  Anomalies: {[str(a) for a in result.anomalies]}")
    
    # Stale data
    stale_data = {
        'symbol': 'EURUSD',
        'open': 1.0850,
        'high': 1.0875,
        'low': 1.0840,
        'close': 1.0860,
        'volume': 1500000,
        'timestamp': datetime.utcnow() - timedelta(hours=1)  # 1 hour old!
    }
    
    result = gate.validate(stale_data, 'ohlcv')
    print(f"\n[STALE DATA]")
    print(f"  Score: {result.score:.2f}")
    print(f"  Usable: {result.is_usable}")
    print(f"  Freshness: {result.freshness:.2f}")


def demo_walk_forward():
    """Demo: Walk-Forward Validation Gate"""
    print_header("WALK-FORWARD VALIDATION GATE")
    
    gate = WalkForwardGate()
    
    # Good strategy - consistent OOS performance
    good_walks = [
        {'is_sharpe': 1.5, 'oos_sharpe': 1.2, 'is_returns': 0.15, 'oos_returns': 0.10,
         'is_drawdown': 0.08, 'oos_drawdown': 0.10, 'is_win_rate': 0.55, 'oos_win_rate': 0.52,
         'is_trades': 50, 'oos_trades': 40},
        {'is_sharpe': 1.4, 'oos_sharpe': 1.1, 'is_returns': 0.12, 'oos_returns': 0.09,
         'is_drawdown': 0.07, 'oos_drawdown': 0.09, 'is_win_rate': 0.54, 'oos_win_rate': 0.51,
         'is_trades': 55, 'oos_trades': 45},
        {'is_sharpe': 1.6, 'oos_sharpe': 1.3, 'is_returns': 0.18, 'oos_returns': 0.12,
         'is_drawdown': 0.09, 'oos_drawdown': 0.11, 'is_win_rate': 0.56, 'oos_win_rate': 0.53,
         'is_trades': 48, 'oos_trades': 38},
        {'is_sharpe': 1.5, 'oos_sharpe': 1.2, 'is_returns': 0.14, 'oos_returns': 0.11,
         'is_drawdown': 0.08, 'oos_drawdown': 0.10, 'is_win_rate': 0.55, 'oos_win_rate': 0.52,
         'is_trades': 52, 'oos_trades': 42},
    ]
    
    result = gate.validate_strategy('good_strategy', good_walks)
    print(f"\n[GOOD STRATEGY]")
    print(f"  Approved: {result.is_approved}")
    print(f"  OOS Sharpe: {result.avg_oos_sharpe:.2f}")
    print(f"  Overfit Score: {result.overfit_score:.2f}")
    print(f"  Confidence: {result.confidence_multiplier:.2f}")
    
    # Overfit strategy - huge IS/OOS gap
    overfit_walks = [
        {'is_sharpe': 3.5, 'oos_sharpe': 0.3, 'is_returns': 0.50, 'oos_returns': 0.02,
         'is_drawdown': 0.02, 'oos_drawdown': 0.15, 'is_win_rate': 0.75, 'oos_win_rate': 0.45,
         'is_trades': 50, 'oos_trades': 40},
        {'is_sharpe': 4.0, 'oos_sharpe': 0.2, 'is_returns': 0.60, 'oos_returns': 0.01,
         'is_drawdown': 0.01, 'oos_drawdown': 0.18, 'is_win_rate': 0.80, 'oos_win_rate': 0.42,
         'is_trades': 55, 'oos_trades': 45},
        {'is_sharpe': 3.8, 'oos_sharpe': 0.1, 'is_returns': 0.55, 'oos_returns': -0.02,
         'is_drawdown': 0.02, 'oos_drawdown': 0.20, 'is_win_rate': 0.78, 'oos_win_rate': 0.40,
         'is_trades': 48, 'oos_trades': 38},
        {'is_sharpe': 3.6, 'oos_sharpe': 0.25, 'is_returns': 0.52, 'oos_returns': 0.01,
         'is_drawdown': 0.02, 'oos_drawdown': 0.16, 'is_win_rate': 0.76, 'oos_win_rate': 0.44,
         'is_trades': 52, 'oos_trades': 42},
    ]
    
    result = gate.validate_strategy('overfit_strategy', overfit_walks)
    print(f"\n[OVERFIT STRATEGY]")
    print(f"  Approved: {result.is_approved}")
    print(f"  OOS Sharpe: {result.avg_oos_sharpe:.2f}")
    print(f"  Overfit Score: {result.overfit_score:.2f}")
    print(f"  Failure Reasons: {result.failure_reasons}")


def demo_execution_realism():
    """Demo: Execution Realism Gate"""
    print_header("EXECUTION REALISM GATE")
    
    gate = ExecutionRealismGate()
    
    # Good trade - sufficient edge after costs
    result = gate.analyze_trade(
        symbol='EURUSD',
        side='buy',
        size=10000,
        price=1.0850,
        expected_return=0.5,  # 0.5% expected return
        volatility=0.15,
        spread=0.0002,
        avg_daily_volume=5000000000
    )
    
    print(f"\n[GOOD TRADE - Sufficient Edge]")
    print(f"  Expected Return: 0.50%")
    print(f"  Adjusted Return: {result.adjusted_return:.2f}%")
    print(f"  Total Cost: {result.total_cost*100:.3f}%")
    print(f"  Viable: {result.is_viable}")
    print(f"  Quality: {result.quality.value}")
    
    # Bad trade - edge eaten by costs
    result = gate.analyze_trade(
        symbol='EURUSD',
        side='buy',
        size=10000,
        price=1.0850,
        expected_return=0.05,  # Only 0.05% expected return
        volatility=0.25,
        spread=0.0005,
        avg_daily_volume=1000000
    )
    
    print(f"\n[BAD TRADE - Edge Eaten by Costs]")
    print(f"  Expected Return: 0.05%")
    print(f"  Adjusted Return: {result.adjusted_return:.2f}%")
    print(f"  Total Cost: {result.total_cost*100:.3f}%")
    print(f"  Viable: {result.is_viable}")
    print(f"  Warnings: {result.warnings}")
    
    # Backtest adjustment
    print(f"\n[BACKTEST REALITY CHECK]")
    adjusted = gate.adjust_backtest_results(
        backtest_returns=25.0,  # 25% backtest returns
        backtest_sharpe=2.5,
        num_trades=500,
        avg_trade_size=10000,
        avg_holding_period_days=2,
        volatility=0.15
    )
    print(f"  Original Returns: {adjusted['original_returns']:.1f}%")
    print(f"  Adjusted Returns: {adjusted['adjusted_returns']:.1f}%")
    print(f"  Original Sharpe: {adjusted['original_sharpe']:.2f}")
    print(f"  Adjusted Sharpe: {adjusted['adjusted_sharpe']:.2f}")
    print(f"  Reality Factor: {adjusted['reality_factor']:.2f}")
    print(f"  Still Profitable: {adjusted['is_still_profitable']}")


def demo_multiple_testing():
    """Demo: Multiple Testing Correction Gate"""
    print_header("MULTIPLE TESTING CORRECTION GATE")
    
    gate = MultipleTestingGate()
    
    # Register a strategy with large search space
    gate.register_test(
        strategy_id='overoptimized_strategy',
        num_parameters=10,
        parameter_ranges={
            'fast_ma': (5, 50),
            'slow_ma': (20, 200),
            'rsi_period': (7, 21),
            'rsi_overbought': (60, 80),
            'rsi_oversold': (20, 40),
        },
        data_hash='dataset_001',
        optimization_method='grid_search'
    )
    
    # Correct results
    result = gate.correct_results(
        strategy_id='overoptimized_strategy',
        observed_sharpe=2.5,  # Looks great!
        observed_pvalue=0.01,  # Significant!
        num_trades=100,
        backtest_years=3
    )
    
    print(f"\n[OVER-OPTIMIZED STRATEGY]")
    print(f"  Original Sharpe: {result.original_sharpe:.2f}")
    print(f"  Deflated Sharpe: {result.deflated_sharpe:.2f}")
    print(f"  Original P-value: {result.original_pvalue:.4f}")
    print(f"  Corrected P-value: {result.corrected_pvalue:.4f}")
    print(f"  Effective Tests: {result.num_tests}")
    print(f"  Is Significant: {result.is_significant}")
    print(f"  Overfit Risk: {result.overfit_risk.value}")
    print(f"  False Discovery Prob: {result.false_discovery_prob:.1%}")
    print(f"  Warnings: {result.warnings}")


def demo_drift_detection():
    """Demo: Drift Detection Gate"""
    print_header("DRIFT DETECTION GATE")
    
    gate = DriftDetectionGate()
    
    # Simulate stable period
    print(f"\n[STABLE PERIOD]")
    for i in range(30):
        status = gate.check_drift(
            features={'trend': 0.2 + i*0.001, 'momentum': 0.1},
            current_volatility=0.15,
            current_regime='trending'
        )
    print(f"  Is Stable: {status.is_stable}")
    print(f"  Drift Score: {status.overall_drift_score:.2f}")
    print(f"  Position Multiplier: {status.position_size_multiplier:.2f}")
    
    # Simulate drift
    print(f"\n[DRIFT PERIOD - Volatility Spike]")
    for i in range(10):
        status = gate.check_drift(
            features={'trend': -0.3, 'momentum': -0.4},
            current_volatility=0.45 + i*0.05,  # Increasing volatility
            current_regime='volatile'
        )
    print(f"  Is Stable: {status.is_stable}")
    print(f"  Drift Score: {status.overall_drift_score:.2f}")
    print(f"  Should Halt: {status.should_halt_trading}")
    print(f"  Active Alerts: {len(status.active_alerts)}")
    for alert in status.active_alerts:
        print(f"    - {alert}")


def demo_kill_switch():
    """Demo: Kill Switch Gate"""
    print_header("KILL SWITCH GATE")
    
    gate = KillSwitchGate()
    
    # Normal operation
    print(f"\n[NORMAL OPERATION]")
    is_allowed, reasons = gate.check(
        current_equity=100000,
        current_return=0.01,
        current_volatility=0.15
    )
    print(f"  Trading Allowed: {is_allowed}")
    print(f"  Status: {gate.status.value}")
    
    # Simulate losses
    print(f"\n[SIMULATING CONSECUTIVE LOSSES]")
    for i in range(6):
        gate.check(
            current_equity=100000 - i*1000,
            trade_result={'pnl': -500}
        )
    
    is_allowed, reasons = gate.check(current_equity=94000)
    print(f"  Trading Allowed: {is_allowed}")
    print(f"  Status: {gate.status.value}")
    print(f"  Reasons: {[r.value for r in reasons]}")
    
    # Reset for next demo
    gate.manual_reset(confirm=True)
    
    # Simulate drawdown
    print(f"\n[SIMULATING DRAWDOWN]")
    gate.peak_equity = 100000
    is_allowed, reasons = gate.check(current_equity=82000)  # 18% drawdown
    print(f"  Trading Allowed: {is_allowed}")
    print(f"  Status: {gate.status.value}")
    print(f"  Reasons: {[r.value for r in reasons]}")


def demo_master_gate():
    """Demo: Master Reality Gate"""
    print_header("MASTER REALITY GATE - FULL INTEGRATION")
    
    gate = create_reality_gate()
    
    # Register a strategy first
    gate.register_strategy(
        strategy_id='demo_strategy',
        num_parameters=5,
        parameter_ranges={'param1': (1, 10), 'param2': (0.1, 0.5)},
        data_hash='demo_data',
        walk_forward_results=[
            {'is_sharpe': 1.5, 'oos_sharpe': 1.2, 'is_returns': 0.15, 'oos_returns': 0.10,
             'is_drawdown': 0.08, 'oos_drawdown': 0.10, 'is_win_rate': 0.55, 'oos_win_rate': 0.52,
             'is_trades': 50, 'oos_trades': 40},
            {'is_sharpe': 1.4, 'oos_sharpe': 1.1, 'is_returns': 0.12, 'oos_returns': 0.09,
             'is_drawdown': 0.07, 'oos_drawdown': 0.09, 'is_win_rate': 0.54, 'oos_win_rate': 0.51,
             'is_trades': 55, 'oos_trades': 45},
            {'is_sharpe': 1.6, 'oos_sharpe': 1.3, 'is_returns': 0.18, 'oos_returns': 0.12,
             'is_drawdown': 0.09, 'oos_drawdown': 0.11, 'is_win_rate': 0.56, 'oos_win_rate': 0.53,
             'is_trades': 48, 'oos_trades': 38},
            {'is_sharpe': 1.5, 'oos_sharpe': 1.2, 'is_returns': 0.14, 'oos_returns': 0.11,
             'is_drawdown': 0.08, 'oos_drawdown': 0.10, 'is_win_rate': 0.55, 'oos_win_rate': 0.52,
             'is_trades': 52, 'oos_trades': 42},
        ]
    )
    
    # Good trade scenario
    print(f"\n[GOOD TRADE SCENARIO]")
    result = gate.check(
        market_data={
            'symbol': 'EURUSD',
            'open': 1.0850,
            'high': 1.0875,
            'low': 1.0840,
            'close': 1.0860,
            'volume': 1500000,
            'timestamp': datetime.utcnow(),
            'return': 0.001
        },
        strategy_id='demo_strategy',
        symbol='EURUSD',
        side='buy',
        size=10000,
        price=1.0860,
        expected_return=0.5,
        current_equity=100000,
        current_volatility=0.15,
        avg_daily_volume=5000000000,
        spread=0.0002,
        features={'trend': 0.2, 'momentum': 0.15}
    )
    
    print(f"  Approved: {result.is_approved}")
    print(f"  Confidence Multiplier: {result.final_confidence_multiplier:.2f}")
    print(f"  Position Size Multiplier: {result.final_position_size_multiplier:.2f}")
    print(f"  Blocking Gates: {result.blocking_gates}")
    print(f"  Warnings: {result.warnings[:3]}")
    
    # Print gate results
    print(f"\n  Gate Results:")
    for gr in result.gate_results:
        print(f"    - {gr.gate_name}: {gr.status.value} ({gr.message[:50]})")
    
    # Bad trade scenario - unvalidated strategy
    print(f"\n[BAD TRADE - UNVALIDATED STRATEGY]")
    result = gate.check(
        market_data={
            'symbol': 'EURUSD',
            'open': 1.0850,
            'high': 1.0875,
            'low': 1.0840,
            'close': 1.0860,
            'volume': 1500000,
            'timestamp': datetime.utcnow()
        },
        strategy_id='unknown_strategy',  # Not registered!
        symbol='EURUSD',
        side='buy',
        size=10000,
        price=1.0860,
        expected_return=0.5,
        current_equity=100000,
        current_volatility=0.15,
        avg_daily_volume=5000000000,
        spread=0.0002
    )
    
    print(f"  Approved: {result.is_approved}")
    print(f"  Blocking Gates: {result.blocking_gates}")
    print(f"  Blocking Reasons: {result.blocking_reasons}")
    
    # Print statistics
    print(f"\n[STATISTICS]")
    stats = gate.get_statistics()
    print(f"  Total Checks: {stats['master_gate']['total_checks']}")
    print(f"  Approved: {stats['master_gate']['total_approved']}")
    print(f"  Blocked: {stats['master_gate']['total_blocked']}")


def main():
    print("\n" + "=" * 60)
    print(" REALITY GATES - PREVENTING AI STUPIDITY IN LIVE TRADING")
    print(" 'In backtest we are geniuses. In live trading, we are humble.'")
    print("=" * 60)
    
    try:
        demo_data_integrity()
        demo_walk_forward()
        demo_execution_realism()
        demo_multiple_testing()
        demo_drift_detection()
        demo_kill_switch()
        demo_master_gate()
        
        print_header("DEMO COMPLETE")
        print("\n[SUCCESS] All reality gates demonstrated!")
        print("\nThe Reality Gates protect against:")
        print("  - Bad/stale/impossible data")
        print("  - Unvalidated strategies")
        print("  - Unrealistic execution assumptions")
        print("  - P-hacking and overfitting")
        print("  - Market regime changes")
        print("  - Catastrophic losses")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
