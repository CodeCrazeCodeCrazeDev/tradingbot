"""
AlphaAlgo Internet-Empowered Trading System Demo
Demonstrates all 5 phases of autonomous internet-powered trading.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.internet_access import AlphaAlgoOrchestrator


async def demo_single_cycle():
    pass
    """
    Demo: Run a single trading cycle
    Shows data acquisition, intelligence fusion, and decision making
    """
    print("\n" + "=" * 80)
    print("DEMO: Single Trading Cycle")
    print("=" * 80 + "\n")
    
    # Create orchestrator
    orchestrator = AlphaAlgoOrchestrator()
    
    try:
    pass
        # Initialize system
        print("Initializing AlphaAlgo system...")
        initialized = await orchestrator.initialize()
        
        if not initialized:
    pass
            print("❌ System initialization failed")
            return
        
        print("\n✅ System initialized successfully\n")
        
        # Run a single trading cycle
        print("Running trading cycle...")
        decision = await orchestrator.run_trading_cycle()
        
        if decision:
    pass
            print("\n" + "=" * 80)
            print("TRADING DECISION SUMMARY")
            print("=" * 80)
            print(f"Symbol:     {decision.symbol}")
            print(f"Action:     {decision.action}")
            print(f"Confidence: {decision.confidence:.2%}")
            print(f"Strength:   {decision.strength:.2f}")
            print(f"Risk Score: {decision.risk_score:.2%}")
            print("\nComponent Signals:")
            for signal_type, signal in decision.component_signals.items():
    pass
                print(f"  {signal_type:12s}: strength={signal.strength:+.2f}, confidence={signal.confidence:.2%}")
            print("=" * 80 + "\n")
        
        # Get system status
        status = orchestrator.get_system_status()
        
        print("\n" + "=" * 80)
        print("SYSTEM STATUS")
        print("=" * 80)
        print(f"Trading Enabled: {status['trading_enabled']}")
        print(f"Symbols:         {', '.join(status['symbols'])}")
        
        print("\nConnection Status:")
        for name, endpoint in status['connections']['endpoints'].items():
    pass
            status_icon = "✅" if endpoint['status'] == 'healthy' else "⚠️"
            print(f"  {status_icon} {name:15s}: {endpoint['status']:10s} (latency: {endpoint['latency_ms']:.1f}ms)")
        
        print("\nFusion Statistics:")
        fusion_stats = status.get('fusion_stats', {})
        if fusion_stats:
    pass
            print(f"  Total Decisions:  {fusion_stats.get('total_decisions', 0)}")
            print(f"  Buy Signals:      {fusion_stats.get('buy_signals', 0)}")
            print(f"  Sell Signals:     {fusion_stats.get('sell_signals', 0)}")
            print(f"  Hold Signals:     {fusion_stats.get('hold_signals', 0)}")
            print(f"  Avg Confidence:   {fusion_stats.get('avg_confidence', 0):.2%}")
        
        print("=" * 80 + "\n")
    
    finally:
    pass
        # Cleanup
        await orchestrator.stop()
        orchestrator.save_status_report('alphaalgo_demo_status.json')
        print("✅ Demo complete. Status saved to alphaalgo_demo_status.json")


async def demo_autonomous_operation(duration_minutes: int = 5):
    pass
    """
    Demo: Run autonomous operation for a specified duration
    Shows continuous monitoring, trading cycles, and auto-updates
    """
    print("\n" + "=" * 80)
    print(f"DEMO: Autonomous Operation ({duration_minutes} minutes)")
    print("=" * 80 + "\n")
    
    # Create orchestrator
    orchestrator = AlphaAlgoOrchestrator()
    
    try:
    pass
        # Start autonomous operation
        operation_task = asyncio.create_task(orchestrator.start_autonomous_operation())
        
        # Let it run for specified duration
        print(f"Running autonomous operation for {duration_minutes} minutes...")
        print("Press Ctrl+C to stop early\n")
        
        await asyncio.sleep(duration_minutes * 60)
        
        print(f"\n⏰ {duration_minutes} minutes elapsed, stopping...")
    
    except KeyboardInterrupt:
    pass
        print("\n⚠️ Interrupted by user")
    
    finally:
    pass
        # Stop operation
        await orchestrator.stop()
        
        # Save final status
        orchestrator.save_status_report('alphaalgo_autonomous_status.json')
        
        # Print summary
        status = orchestrator.get_system_status()
        
        print("\n" + "=" * 80)
        print("AUTONOMOUS OPERATION SUMMARY")
        print("=" * 80)
        
        fusion_stats = status.get('fusion_stats', {})
        if fusion_stats:
    pass
            print(f"Total Decisions Made:  {fusion_stats.get('total_decisions', 0)}")
            print(f"  - Buy Signals:       {fusion_stats.get('buy_signals', 0)}")
            print(f"  - Sell Signals:      {fusion_stats.get('sell_signals', 0)}")
            print(f"  - Hold Signals:      {fusion_stats.get('hold_signals', 0)}")
            print(f"Average Confidence:    {fusion_stats.get('avg_confidence', 0):.2%}")
            print(f"High Confidence %:     {fusion_stats.get('high_confidence_pct', 0):.1f}%")
        
        updater_stats = status.get('auto_updater', {})
        if updater_stats:
    pass
            print(f"\nAuto-Updater:")
            print(f"  Total Cycles:        {updater_stats.get('total_cycles', 0)}")
            print(f"  Successful:          {updater_stats.get('successful_cycles', 0)}")
            print(f"  Failed:              {updater_stats.get('failed_cycles', 0)}")
        
        print("=" * 80)
        print("✅ Status saved to alphaalgo_autonomous_status.json\n")


async def demo_phase_by_phase():
    pass
    """
    Demo: Show each phase individually
    Educational demo showing how each component works
    """
    print("\n" + "=" * 80)
    print("DEMO: Phase-by-Phase Walkthrough")
    print("=" * 80 + "\n")
    
    from trading_bot.internet_access import (
from enum import auto
import json
        ConnectionValidator,
        DataAcquisitionEngine,
        IntelligenceFusionEngine,
        SecurityManager,
        AutoUpdater
    )
    
    config = {
        'connections': {'endpoints': {}},
        'data_acquisition': {'endpoints': {}, 'api_keys': {}},
        'fusion': {
            'fusion_weights': {'technical': 0.6, 'sentiment': 0.25, 'news': 0.1, 'volatility': 0.05},
            'min_confidence': 0.6
        },
        'security': {'secure_dir': 'secure'},
        'auto_update': {
            'models_dir': 'models',
            'archive_dir': 'models/archive',
            'update_log': 'update_report.log',
            'update_interval_hours': 24,
            'min_performance': 0.70
        }
    }
    
    # Phase 1: Connection Validation
    print("=" * 80)
    print("PHASE 1: Connection Validation")
    print("=" * 80)
    
    validator = ConnectionValidator(config['connections'])
    print("✓ Connection validator initialized")
    print(f"  Monitoring {len(validator.endpoints)} endpoints")
    
    # Phase 2: Data Acquisition
    print("\n" + "=" * 80)
    print("PHASE 2: Data Acquisition")
    print("=" * 80)
    
    data_engine = DataAcquisitionEngine(config['data_acquisition'])
    print("✓ Data acquisition engine initialized")
    
    symbols = ['EURUSD']
    print(f"\nFetching data for {symbols}...")
    data_package = await data_engine.acquire_all_data(symbols)
    
    print(f"✓ Data acquired:")
    print(f"  - Market data timeframes: {len(data_package.get('market_data', {}))}")
    print(f"  - News articles:          {len(data_package.get('news', []))}")
    print(f"  - Sentiment symbols:      {len(data_package.get('sentiment', {}))}")
    print(f"  - Macro indicators:       {len(data_package.get('macro', {}))}")
    
    # Phase 3: Intelligence Fusion
    print("\n" + "=" * 80)
    print("PHASE 3: Intelligence Fusion")
    print("=" * 80)
    
    fusion_engine = IntelligenceFusionEngine(config['fusion'])
    print("✓ Intelligence fusion engine initialized")
    print(f"  Fusion weights: {config['fusion']['fusion_weights']}")
    
    print("\nProcessing data package...")
    decision = fusion_engine.process_data_package(data_package, symbols[0])
    
    print(f"\n✓ Decision generated:")
    print(f"  Action:     {decision.action}")
    print(f"  Confidence: {decision.confidence:.2%}")
    print(f"  Strength:   {decision.strength:.2f}")
    
    # Phase 4: Security
    print("\n" + "=" * 80)
    print("PHASE 4: Security & Privacy")
    print("=" * 80)
    
    security = SecurityManager(config['security'])
    print("✓ Security manager initialized")
    
    # Check URL safety
    test_url = "https://api.example.com/data"
    is_safe, msg = security.check_url_safety(test_url)
    print(f"\nURL Safety Check: {test_url}")
    print(f"  Result: {'✓ Safe' if is_safe else '✗ Unsafe'}")
    
    security_report = security.get_security_report()
    print(f"\nSecurity Events: {security_report.get('total_events', 0)}")
    
    # Phase 5: Auto-Update
    print("\n" + "=" * 80)
    print("PHASE 5: Auto-Update & Self-Learning")
    print("=" * 80)
    
    updater = AutoUpdater(config['auto_update'])
    print("✓ Auto-updater initialized")
    print(f"  Update interval: {config['auto_update']['update_interval_hours']} hours")
    print(f"  Min performance: {config['auto_update']['min_performance']:.0%}")
    
    print("\nRunning update cycle (simulated)...")
    cycle = await updater.run_update_cycle()
    
    print(f"\n✓ Update cycle complete:")
    print(f"  Cycle ID:          {cycle.cycle_id}")
    print(f"  Success:           {cycle.success}")
    print(f"  Data Fetched:      {cycle.data_fetched}")
    print(f"  Models Retrained:  {cycle.models_retrained}")
    
    print("\n" + "=" * 80)
    print("✅ Phase-by-Phase Demo Complete")
    print("=" * 80 + "\n")


async def main():
    pass
    """Main demo menu"""
    print("\n" + "=" * 80)
    print("ALPHAALGO INTERNET-EMPOWERED TRADING SYSTEM")
    print("Demonstration Suite")
    print("=" * 80)
    
    print("\nAvailable Demos:")
    print("1. Single Trading Cycle (quick demo)")
    print("2. Autonomous Operation (5 minutes)")
    print("3. Phase-by-Phase Walkthrough (educational)")
    print("4. Run All Demos")
    
    choice = input("\nSelect demo (1-4) or 'q' to quit: ").strip()
    
    if choice == '1':
    pass
        await demo_single_cycle()
    elif choice == '2':
    pass
        await demo_autonomous_operation(duration_minutes=5)
    elif choice == '3':
    pass
        await demo_phase_by_phase()
    elif choice == '4':
    pass
        await demo_phase_by_phase()
        await demo_single_cycle()
        print("\nSkipping autonomous operation demo (would run for 5 minutes)")
        print("Run demo 2 separately to see autonomous operation")
    elif choice.lower() == 'q':
    pass
        print("Exiting...")
        return
    else:
    pass
        print("Invalid choice")
        return
    
    print("\n✅ All demos complete!")


if __name__ == '__main__':
    pass
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('alphaalgo_demo.log')
        ]
    )
    
    # Run demos
    try:
    pass
        asyncio.run(main())
    except KeyboardInterrupt:
    pass
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
    pass
        print(f"\n❌ Error: {e}")
        logging.exception("Demo error")
