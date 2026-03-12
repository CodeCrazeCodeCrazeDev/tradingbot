"""
Module Integration Demo
Demonstrates the unified module integration system.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot import (
    MasterOrchestrator,
    OrchestratorConfig,
    initialize_registry,
    get_registry,
    get_orchestrator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main demo function."""
    print("=" * 60)
    print("TRADING BOT MODULE INTEGRATION DEMO")
    print("=" * 60)
    
    # 1. Initialize Registry
    print("\n1. Initializing Module Registry...")
    registry = await initialize_registry()
    
    stats = registry.get_statistics()
    print(f"   - Total modules discovered: {stats['total_modules']}")
    print(f"   - Enabled modules: {stats['enabled_modules']}")
    print(f"   - Categories: {list(stats['categories'].keys())}")
    
    # Show modules by category
    for category, info in stats['categories'].items():
        if info['total'] > 0:
            print(f"   - {category}: {info['total']} modules")
    
    # 2. Create Orchestrator Configuration
    print("\n2. Creating Orchestrator Configuration...")
    config = OrchestratorConfig(
        mode="paper",
        auto_start=False,
        enable_optional_modules=True,
        parallel_init=True,
        health_check_interval=30.0,
        symbols=["EURUSD", "GBPUSD"],
        timeframes=["M5", "M15", "H1"],
        enable_ai_features=True,
        enable_ml_features=True,
        enable_evolution_features=False,
        enable_sentient_features=False
    )
    
    print(f"   - Trading mode: {config.mode}")
    print(f"   - Symbols: {config.symbols}")
    print(f"   - AI features: {config.enable_ai_features}")
    print(f"   - ML features: {config.enable_ml_features}")
    
    # 3. Initialize Master Orchestrator
    print("\n3. Initializing Master Orchestrator...")
    orchestrator = get_orchestrator()
    
    success = await orchestrator.initialize(config)
    
    if success:
        print("   ✓ Orchestrator initialized successfully")
    else:
        print("   ✗ Failed to initialize orchestrator")
        return
    
    # 4. Show System Status
    print("\n4. System Status:")
    status = orchestrator.get_status()
    
    print(f"   - Initialized: {status['initialized']}")
    print(f"   - Running: {status['running']}")
    print(f"   - Mode: {status['mode']}")
    
    if 'uptime' in status and status['uptime']:
        print(f"   - Uptime: {status['uptime']:.2f} seconds")
    
    print("\n   Service Managers:")
    for name, manager_status in status['service_managers'].items():
        print(f"   - {name}:")
        print(f"     - Initialized: {manager_status['initialized']}")
        print(f"     - Services: {manager_status['service_count']}")
        print(f"     - Healthy: {manager_status['healthy_services']}/{manager_status['service_count']}")
    
    # 5. Start the System
    print("\n5. Starting Trading System...")
    success = await orchestrator.start()
    
    if success:
        print("   ✓ System started successfully")
    else:
        print("   ✗ Failed to start system")
        return
    
    # 6. Process a Sample Signal
    print("\n6. Processing Sample Signal...")
    sample_signal = {
        'id': 'demo_signal_001',
        'symbol': 'EURUSD',
        'direction': 'buy',
        'confidence': 0.75,
        'price': 1.0850,
        'strategy': 'demo_strategy',
        'timestamp': datetime.now().isoformat()
    }
    
    result = await orchestrator.process_signal(sample_signal)
    print(f"   - Signal result: {result.get('status', 'unknown')}")
    if result.get('message'):
        print(f"   - Message: {result['message']}")
    
    # 7. Monitor for a Few Seconds
    print("\n7. Monitoring System (5 seconds)...")
    await asyncio.sleep(5)
    
    # Show updated status
    updated_status = orchestrator.get_status()
    print(f"   - Events processed: {updated_status['metrics']['events_processed']}")
    print(f"   - Errors count: {updated_status['metrics']['errors_count']}")
    
    # 8. Export System State
    print("\n8. Exporting System State...")
    state_file = "demo_system_state.json"
    success = await orchestrator.export_state(state_file)
    
    if success:
        print(f"   ✓ State exported to {state_file}")
    else:
        print("   ✗ Failed to export state")
    
    # 9. Shutdown
    print("\n9. Shutting Down...")
    await orchestrator.shutdown()
    print("   ✓ System shutdown complete")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\nIntegration Summary:")
    print(f"✓ Module Registry: {stats['total_modules']} modules discovered")
    print(f"✓ Service Managers: {len(status['service_managers'])} managers initialized")
    print(f"✓ Event Bus: {status['event_bus']['events_published']} events published")
    print(f"✓ System successfully integrated and operational")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        print(f"\nDemo failed: {e}")
