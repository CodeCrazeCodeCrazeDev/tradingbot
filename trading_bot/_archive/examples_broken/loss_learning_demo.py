"""
Loss Learning Self-Improvement Engine Demo
Demonstrates automated learning from losing trades with conservative safety controls.
"""

import asyncio
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.self_improvement import (
    SelfImprovementEngine,
    TradeTriage,
    LossCategory
)


def load_config():
    pass
    """Load configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'loss_learning_config.yaml'
    with open(config_path, 'r') as f:
    pass
        return yaml.safe_load(f)


def create_sample_losing_trade():
    pass
    """Create a sample losing trade for demonstration."""
    return {
        'ticket_id': 'DEMO_12345',
        'entry_time': datetime.now() - timedelta(hours=2),
        'exit_time': datetime.now(),
        'symbol': 'EURUSD',
        'side': 'buy',
        'entry_price': 1.1000,
        'exit_price': 1.0980,  # Lost 20 pips
        'size': 0.1,
        'sl': 1.0990,  # Stop loss hit
        'tp': 1.1040,
        'pnl': -20.0,
        'fees': 0.50,
        'slippage': 0.0003,  # 0.03% slippage
        'execution_latency_ms': 150
    }


def create_sample_signal_data():
    pass
    """Create sample signal context."""
    return {
        'indicators_used': ['RSI', 'MACD', 'EMA'],
        'indicator_values': {
            'RSI': 65,
            'MACD': 0.0015,
            'EMA_20': 1.0995,
            'EMA_50': 1.0990
        },
        'model_confidence': 0.45,  # Low confidence!
        'timeframe': 'H1',
        'market_regime': 'ranging',
        'multi_tf_agreement': False,  # Disagreement!
        'signal_drift': 0.35  # High drift!
    }


def create_sample_market_data():
    pass
    """Create sample market data snapshot."""
    return {
        'candles_before': [
            {'time': datetime.now() - timedelta(hours=i), 'open': 1.1000 + i*0.0001, 
             'high': 1.1005 + i*0.0001, 'low': 1.0995 + i*0.0001, 'close': 1.1000 + i*0.0001}
            for i in range(10, 0, -1)
        ],
        'candles_after': [
            {'time': datetime.now() + timedelta(minutes=i*15), 'open': 1.0995 - i*0.0002,
             'high': 1.1000 - i*0.0002, 'low': 1.0990 - i*0.0002, 'close': 1.0995 - i*0.0002}
            for i in range(1, 6)
        ],
        'atr': 0.0015,  # 15 pips ATR
        'spread': 0.00015,  # 1.5 pips spread
        'volume_avg': 1000,
        'volatility_spike': False,
        'news_events': []
    }


def create_sample_system_data():
    pass
    """Create sample system metrics."""
    return {
        'cpu_usage': 45.0,
        'memory_usage': 60.0,
        'latency_ms': 150,
        'order_fill_type': 'full',
        'errors_in_logs': []
    }


async def demo_basic_workflow():
    pass
    """Demonstrate basic self-improvement workflow."""
    print("=" * 80)
    print("SELF-IMPROVEMENT ENGINE DEMO")
    print("=" * 80)
    print()
    
    # Load configuration
    print("1. Loading configuration...")
    config = load_config()
    print(f"   AUTO_LEARN: {config['AUTO_LEARN']}")
    print(f"   CONF_THRESHOLD: {config['CONF_THRESHOLD']}")
    print(f"   AUTO_PROMOTE: {config['AUTO_PROMOTE']}")
    print()
    
    # Initialize engine
    print("2. Initializing Self-Improvement Engine...")
    engine = SelfImprovementEngine(config)
    print("   ✓ Engine initialized")
    print()
    
    # Create sample data
    print("3. Creating sample losing trade...")
    trade = create_sample_losing_trade()
    signal_data = create_sample_signal_data()
    market_data = create_sample_market_data()
    system_data = create_sample_system_data()
    equity = 10000.0
    
    print(f"   Trade: {trade['symbol']} {trade['side']}")
    print(f"   PnL: ${trade['pnl']:.2f}")
    print(f"   Signal Confidence: {signal_data['model_confidence']:.2f}")
    print(f"   Multi-TF Agreement: {signal_data['multi_tf_agreement']}")
    print()
    
    # Process losing trade
    print("4. Processing losing trade through self-improvement pipeline...")
    print()
    
    result = engine.process_losing_trade(
        trade=trade,
        signal_data=signal_data,
        market_data=market_data,
        system_data=system_data,
        equity=equity
    )
    
    # Display results
    print("5. Results:")
    print(f"   Status: {result['status']}")
    
    if result['status'] == 'processed':
    pass
        print(f"   Trade ID: {result['trade_id']}")
        print(f"   Hypotheses Generated: {result['hypotheses_count']}")
        print(f"   Fixes Proposed: {result['fixes_proposed']}")
        print(f"   Git Branch: {result['branch']}")
        print()
        
        # Show diagnostic details
        diagnostic = result['diagnostic']
        print("   Diagnostic Details:")
        print(f"     Loss Category: {diagnostic['loss_category']}")
        print(f"     PnL %: {diagnostic['pnl_pct']*100:.2f}%")
        print(f"     Anomalies Detected: {len(diagnostic['anomalies'])}")
        
        if diagnostic['anomalies']:
    pass
            print("     Anomalies:")
            for anomaly in diagnostic['anomalies']:
    pass
                print(f"       - {anomaly}")
        print()
        
        # Show canary results
        if result['canary_results']:
    pass
            print("   Canary Validations Started:")
            for canary in result['canary_results']:
    pass
                print(f"     - Fix: {canary['fix_id']}")
                print(f"       Canary ID: {canary['canary_id']}")
                print(f"       Duration: {canary['duration_minutes']} minutes")
            print()
    
    elif result['status'] == 'escalated':
    pass
        print(f"   Reason: {result['reason']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print("   ⚠ Escalated to human review")
        print()
    
    # Show system status
    print("6. System Status:")
    status = engine.get_status()
    print(f"   Labeled Examples: {status['labeled_examples']}")
    print(f"   Ready for Retrain: {status['ready_for_retrain']}")
    print(f"   Current Model Version: {status['current_model_version']}")
    print(f"   Active Canaries: {status['active_canaries']}")
    print()
    
    # Show audit summary
    print("7. Audit Summary:")
    audit = status['audit_summary']
    print(f"   Triage Diagnostics: {audit.get('triage_diagnostics', 0)}")
    print(f"   Root Cause Analyses: {audit.get('root_cause_analyses', 0)}")
    print(f"   Fixes Proposed: {audit.get('fixes_proposed', 0)}")
    print(f"   Canary Validations: {audit.get('canary_validations', 0)}")
    print(f"   Fixes Applied: {audit.get('fixes_applied', 0)}")
    print(f"   Rollbacks: {audit.get('rollbacks', 0)}")
    print(f"   Escalations: {audit.get('escalations', 0)}")
    print()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Review audit logs in: diagnostics/self_improve/")
    print("2. Check changes log: diagnostics/changes-log.txt")
    print("3. Monitor canary validations")
    print("4. Review and approve fixes if AUTO_PROMOTE=false")
    print()


async def demo_multiple_scenarios():
    pass
    """Demonstrate multiple loss scenarios."""
    print("\n" + "=" * 80)
    print("MULTIPLE SCENARIO DEMO")
    print("=" * 80 + "\n")
    
    config = load_config()
    engine = SelfImprovementEngine(config)
    
    scenarios = [
        {
            'name': 'Low Confidence Signal',
            'signal_confidence': 0.35,
            'multi_tf_agreement': True,
            'slippage': 0.0001
        },
        {
            'name': 'High Slippage',
            'signal_confidence': 0.75,
            'multi_tf_agreement': True,
            'slippage': 0.008  # 0.8% slippage!
        },
        {
            'name': 'Stop Loss Too Tight',
            'signal_confidence': 0.65,
            'multi_tf_agreement': True,
            'slippage': 0.0002,
            'atr': 0.0025,  # High ATR
            'sl_distance': 0.0010  # SL only 0.4x ATR
        },
        {
            'name': 'Multi-Timeframe Disagreement',
            'signal_confidence': 0.70,
            'multi_tf_agreement': False,  # Disagreement
            'slippage': 0.0002
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
    pass
        print(f"\nScenario {i}: {scenario['name']}")
        print("-" * 40)
        
        # Create trade with scenario parameters
        trade = create_sample_losing_trade()
        trade['ticket_id'] = f'DEMO_{i:05d}'
        
        signal_data = create_sample_signal_data()
        signal_data['model_confidence'] = scenario['signal_confidence']
        signal_data['multi_tf_agreement'] = scenario['multi_tf_agreement']
        
        market_data = create_sample_market_data()
        if 'atr' in scenario:
    pass
            market_data['atr'] = scenario['atr']
        
        system_data = create_sample_system_data()
        
        trade['slippage'] = scenario['slippage']
        
        # Process
        result = engine.process_losing_trade(
            trade, signal_data, market_data, system_data, 10000.0
        )
        
        print(f"Status: {result['status']}")
        if result['status'] == 'processed':
    pass
            print(f"Fixes Proposed: {result['fixes_proposed']}")
        elif result['status'] == 'escalated':
    pass
            print(f"Escalation Reason: {result['reason']}")
        
        await asyncio.sleep(0.5)  # Small delay between scenarios
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    pass
    print("\nLoss Learning Self-Improvement Engine")
    print("Conservative, Auditable, Reversible\n")
    
    # Run basic demo
    asyncio.run(demo_basic_workflow())
    
    # Optionally run multiple scenarios
    print("\nRun multiple scenario demo? (y/n): ", end='')
    if input().lower() == 'y':
    pass
        asyncio.run(demo_multiple_scenarios())
    
    print("\nDemo complete. Check diagnostics/self_improve/ for audit logs.")
