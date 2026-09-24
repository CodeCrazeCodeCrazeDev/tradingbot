"""
AlphaAlgo AI System Supervisor Demo
Demonstrates self-healing, monitoring, and autonomous operation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.system_supervisor import SystemSupervisor


async def demo_full_system():
    pass
    """
    Demo: Full system with all phases
    """
    print("\n" + "=" * 80)
    print("🤖 ALPHAALGO AI SYSTEM SUPERVISOR - FULL DEMO")
    print("=" * 80 + "\n")
    
    # Configuration
    config = {
        'internet': {
            'primary_endpoints': [
                'api.broker.com',
                'api.marketdata.com',
                'newsapi.org'
            ],
            'backup_endpoints': ['8.8.8.8', '1.1.1.1'],
            'failover_enabled': True,
            'max_retries': 5,
            'recovery_log': 'logs/network_recovery.log'
        },
        'modules': {
            'check_interval': 30,
            'stale_threshold': 300,
            'max_restart_attempts': 3
        },
        'repair': {
            'backup_dir': 'bot_backups',
            'backup_sources': {
                'market_data': ['alpha_vantage', 'yahoo_finance'],
                'news': ['newsapi', 'finnhub'],
                'sentiment': ['twitter_api', 'reddit_api']
            }
        },
        'data_validation': {
            'price_change_threshold': 0.10,
            'max_data_age': 300,
            'data_providers': {
                'market_data': ['primary', 'backup1', 'backup2'],
                'news': ['newsapi', 'finnhub'],
                'sentiment': ['twitter', 'reddit']
            }
        },
        'check_interval': 60,
        'status_log': 'logs/system_status.log'
    }
    
    # Create supervisor
    supervisor = SystemSupervisor(config)
    
    try:
    pass
        # Start system
        print("Starting AI System Supervisor...\n")
        started = await supervisor.start()
        
        if not started:
    pass
            print("❌ System failed to start")
            return
        
        print("\n✅ System started successfully\n")
        
        # Run for demonstration period
        print("Running system for 5 minutes...")
        print("Monitoring all phases:\n")
        print("  🌐 Phase 1: Internet Health")
        print("  📡 Phase 2: Module Monitoring")
        print("  🔧 Phase 3: Auto-Repair")
        print("  📊 Phase 4: Data Validation")
        print("  🔄 Phase 5: Auto-Update (background)")
        print("  🔒 Phase 6: Security")
        print("  ✅ Phase 7: Stability Confirmation")
        print("\nPress Ctrl+C to stop early\n")
        
        # Monitor for 5 minutes
        for i in range(5):
    pass
            await asyncio.sleep(60)
            
            # Get status
            status = await supervisor.get_system_status()
            
            print(f"\n{'=' * 80}")
            print(f"STATUS UPDATE - Minute {i+1}/5")
            print(f"{'=' * 80}")
            print(f"System Health:    {status.health.value.upper()}")
            print(f"Trading Mode:     {status.trading_mode.value.upper()}")
            print(f"Internet Health:  {status.internet_health:.1f}%")
            print(f"Modules Healthy:  {status.modules_healthy}/{status.modules_total}")
            print(f"Data Validity:    {status.data_validity_pct:.1f}%")
            print(f"Uptime:           {status.uptime_pct:.1f}%")
            
            if status.critical_warnings:
    pass
                print(f"\n⚠️ WARNINGS:")
                for warning in status.critical_warnings:
    pass
                    print(f"   - {warning}")
            
            print(f"{'=' * 80}\n")
        
        print("\n✅ Demo completed successfully")
        
        # Generate final report
        print("\nGenerating comprehensive report...")
        supervisor.save_report('system_supervisor_demo_report.json')
        print("✅ Report saved to: system_supervisor_demo_report.json")
    
    except KeyboardInterrupt:
    pass
        print("\n\n⚠️ Demo interrupted by user")
    
    except Exception as e:
    pass
        print(f"\n❌ Error: {e}")
        logging.exception("Demo error")
    
    finally:
    pass
        # Stop system
        print("\n🛑 Stopping system...")
        await supervisor.stop()
        print("✅ System stopped\n")


async def demo_phase_by_phase():
    pass
    """
    Demo: Show each phase individually
    """
    print("\n" + "=" * 80)
    print("🤖 ALPHAALGO AI SYSTEM SUPERVISOR - PHASE-BY-PHASE DEMO")
    print("=" * 80 + "\n")
    
    from trading_bot.system_supervisor import (
        InternetHealthValidator,
        ModuleMonitor,
        AutoRepairSystem,
        DataValidator
    )
    
    config = {
        'primary_endpoints': ['api.broker.com'],
        'backup_endpoints': ['8.8.8.8'],
        'failover_enabled': True,
        'max_retries': 3
    }
    
    # Phase 1: Internet Health
    print("=" * 80)
    print("🌐 PHASE 1: Internet Health Validation")
    print("=" * 80)
    
    validator = InternetHealthValidator(config)
    metrics = await validator.run_complete_test()
    
    print(f"\n✅ Internet Health: {metrics.health.value.upper()}")
    print(f"   Latency: {metrics.latency_ms:.1f}ms")
    print(f"   Packet Loss: {metrics.packet_loss_pct:.1f}%")
    print(f"   DNS Resolution: {metrics.dns_resolution_ms:.1f}ms")
    print(f"   Meets Thresholds: {'✅ YES' if metrics.meets_thresholds() else '❌ NO'}")
    
    # Phase 2: Module Monitoring
    print("\n" + "=" * 80)
    print("📡 PHASE 2: Module Monitoring")
    print("=" * 80)
    
    monitor = ModuleMonitor({'check_interval': 30})
    
    print("\n✅ Module Monitor initialized")
    print(f"   Monitoring {len(monitor.CRITICAL_MODULES)} critical modules:")
    for module in monitor.CRITICAL_MODULES:
    pass
        print(f"   - {module}")
    
    # Phase 3: Auto-Repair
    print("\n" + "=" * 80)
    print("🔧 PHASE 3: Auto-Repair System")
    print("=" * 80)
    
    repair = AutoRepairSystem({'backup_dir': 'bot_backups'})
    
    print("\n✅ Auto-Repair System initialized")
    print("   Capabilities:")
    print("   - Diagnose failures")
    print("   - Clear cache")
    print("   - Refresh API tokens")
    print("   - Restore from backup")
    print("   - Adapt to API changes")
    print("   - Automatic failover")
    
    # Phase 4: Data Validation
    print("\n" + "=" * 80)
    print("📊 PHASE 4: Data Validation")
    print("=" * 80)
    
    data_validator = DataValidator({
        'price_change_threshold': 0.10,
        'max_data_age': 300
    })
    
    print("\n✅ Data Validator initialized")
    print("   Validation checks:")
    print("   - Missing timestamps")
    print("   - Invalid price values")
    print("   - OHLC consistency")
    print("   - Extreme price changes")
    print("   - Volume validation")
    print("   - JSON structure")
    
    print("\n" + "=" * 80)
    print("✅ ALL PHASES INITIALIZED")
    print("=" * 80 + "\n")


async def demo_self_healing():
    pass
    """
    Demo: Self-healing capabilities
    """
    print("\n" + "=" * 80)
    print("🔧 ALPHAALGO AI SYSTEM - SELF-HEALING DEMO")
    print("=" * 80 + "\n")
    
    from trading_bot.system_supervisor import AutoRepairSystem, FailureType
import json
    
    repair = AutoRepairSystem({'backup_dir': 'bot_backups'})
    
    # Simulate various failures and repairs
    failures = [
        (FailureType.API_RATE_LIMIT, "data_feed"),
        (FailureType.MALFORMED_DATA, "news_fetcher"),
        (FailureType.NETWORK_TIMEOUT, "api_connector"),
    ]
    
    print("Simulating failures and repairs:\n")
    
    for failure_type, module in failures:
    pass
        print(f"{'=' * 80}")
        print(f"Failure: {failure_type.value} in {module}")
        print(f"{'=' * 80}")
        
        # Repair
        success = await repair.repair(module, failure_type)
        
        if success:
    pass
            print(f"✅ Repair successful for {module}")
        else:
    pass
            print(f"❌ Repair failed for {module}")
        
        print()
    
    # Show repair history
    print(f"{'=' * 80}")
    print("REPAIR HISTORY")
    print(f"{'=' * 80}")
    
    history = repair.get_repair_history()
    for action in history:
    pass
        print(f"  {action['timestamp']}: {action['module']} - {action['action']}")
        print(f"    Result: {'✅ Success' if action['success'] else '❌ Failed'}")
    
    print()


async def main():
    pass
    """Main demo menu"""
    print("\n" + "=" * 80)
    print("🤖 ALPHAALGO AI SYSTEM SUPERVISOR")
    print("Demonstration Suite")
    print("=" * 80)
    
    print("\nAvailable Demos:")
    print("1. Full System Demo (5 minutes)")
    print("2. Phase-by-Phase Walkthrough")
    print("3. Self-Healing Capabilities")
    print("4. Run All Demos")
    
    choice = input("\nSelect demo (1-4) or 'q' to quit: ").strip()
    
    if choice == '1':
    pass
        await demo_full_system()
    elif choice == '2':
    pass
        await demo_phase_by_phase()
    elif choice == '3':
    pass
        await demo_self_healing()
    elif choice == '4':
    pass
        await demo_phase_by_phase()
        await demo_self_healing()
        print("\nSkipping full system demo (would run for 5 minutes)")
        print("Run demo 1 separately to see full system operation")
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
            logging.FileHandler('system_supervisor_demo.log')
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
