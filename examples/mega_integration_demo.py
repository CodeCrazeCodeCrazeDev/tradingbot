"""
MEGA Integration Demo
=====================

Demonstrates the complete unified trading system with all 150+ modules.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bot.mega_integration import (
    MegaIntegration, MegaConfig, SystemMode, SystemHealth,
    create_mega_system, quick_start
)


async def demo_basic_initialization():
    """Demo: Basic system initialization"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Initialization")
    print("=" * 70)
    
    # Create system with default config
    system = create_mega_system()
    
    print(f"\nSystem Health: {system.health.value}")
    print(f"Active Modules: {len(system.active_modules)}")
    print(f"Failed Modules: {len(system.failed_modules)}")
    
    # Get module stats
    stats = system.get_module_stats()
    print("\nModule Statistics by Category:")
    for category, data in stats.items():
        print(f"  {category.upper()}: {data['active']}/{data['total']} active")
    
    return system


async def demo_custom_config():
    """Demo: Custom configuration"""
    print("\n" + "=" * 70)
    print("DEMO 2: Custom Configuration")
    print("=" * 70)
    
    config = MegaConfig(
        mode=SystemMode.PAPER,
        symbols=["BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD"],
        initial_capital=250000.0,
        max_risk_per_trade=0.01,  # 1%
        max_daily_loss=0.03,      # 3%
        enable_sentiment=True,
        enable_alternative_data=True,
        enable_deepchart=True,
        enable_systems_ai=True
    )
    
    system = MegaIntegration(config)
    
    print(f"\nConfiguration:")
    print(f"  Mode: {config.mode.value}")
    print(f"  Symbols: {config.symbols}")
    print(f"  Capital: ${config.initial_capital:,.2f}")
    print(f"  Max Risk/Trade: {config.max_risk_per_trade*100}%")
    print(f"  Max Daily Loss: {config.max_daily_loss*100}%")
    
    return system


async def demo_module_access():
    """Demo: Accessing individual modules"""
    print("\n" + "=" * 70)
    print("DEMO 3: Module Access")
    print("=" * 70)
    
    system = create_mega_system()
    
    # List some key modules
    key_modules = [
        'complete_signal_system',
        'complete_execution_system',
        'complete_risk_system',
        'alpha_engine',
        'cognitive_core',
        'deepchart_orchestrator'
    ]
    
    print("\nKey Module Status:")
    for module_name in key_modules:
        module = system.get_module(module_name)
        if module:
            print(f"  ✓ {module_name}: Available")
        else:
            print(f"  ✗ {module_name}: Not loaded")
    
    return system


async def demo_signal_generation():
    """Demo: Signal generation"""
    print("\n" + "=" * 70)
    print("DEMO 4: Signal Generation")
    print("=" * 70)
    
    system = create_mega_system()
    await system.initialize()
    
    # Generate signals for different symbols
    symbols = ["BTCUSDT", "ETHUSDT", "EURUSD"]
    
    print("\nGenerating signals...")
    for symbol in symbols:
        signal = await system._generate_unified_signal(symbol)
        print(f"\n{symbol}:")
        print(f"  Action: {signal.action}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Source: {signal.source}")
        if signal.metadata.get('signals'):
            print(f"  Contributing sources: {len(signal.metadata['signals'])}")
    
    return system


async def demo_status_reporting():
    """Demo: System status reporting"""
    print("\n" + "=" * 70)
    print("DEMO 5: Status Reporting")
    print("=" * 70)
    
    system = create_mega_system()
    
    status = system.get_status()
    
    print(f"\nSystem Status:")
    print(f"  Health: {status.health.value.upper()}")
    print(f"  Mode: {status.mode.value}")
    print(f"  Active Modules: {status.active_modules}/{status.total_modules}")
    print(f"  Failed Modules: {status.failed_modules}")
    print(f"  Uptime: {status.uptime_seconds:.1f}s")
    print(f"  Signals Generated: {status.signals_generated}")
    print(f"  Trades Executed: {status.trades_executed}")
    print(f"  Capital: ${status.capital:,.2f}")
    
    if status.errors:
        print(f"\nRecent Errors ({len(status.errors)}):")
        for error in status.errors[:3]:
            print(f"  - {error[:80]}...")
    
    return system


async def demo_full_list():
    """Demo: Full module listing"""
    print("\n" + "=" * 70)
    print("DEMO 6: Full Module Listing")
    print("=" * 70)
    
    system = create_mega_system()
    
    modules = system.list_modules()
    
    # Group by category
    by_category = {}
    for name, info in modules.items():
        cat = info['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append((name, info))
    
    print(f"\nTotal Modules: {len(modules)}")
    print("\nModules by Category:")
    
    for category, module_list in sorted(by_category.items()):
        print(f"\n  {category.upper()} ({len(module_list)} modules):")
        for name, info in module_list[:5]:  # Show first 5
            status = "✓" if info['health'] else "✗"
            print(f"    {status} {name}")
        if len(module_list) > 5:
            print(f"    ... and {len(module_list) - 5} more")
    
    return system


async def demo_quick_start():
    """Demo: Quick start helper"""
    print("\n" + "=" * 70)
    print("DEMO 7: Quick Start")
    print("=" * 70)
    
    print("\nUsing quick_start() helper...")
    
    system = await quick_start({
        'mode': 'paper',
        'symbols': ['BTCUSDT'],
        'initial_capital': 50000.0
    })
    
    print(f"\nSystem ready!")
    print(f"  Health: {system.health.value}")
    print(f"  Modules: {len(system.active_modules)} active")
    
    return system


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("MEGA INTEGRATION - COMPREHENSIVE DEMO")
    print("=" * 70)
    print("\nThis demo showcases the complete unified trading system")
    print("with 150+ modules and 300+ features.\n")
    
    # Run demos
    await demo_basic_initialization()
    await demo_custom_config()
    await demo_module_access()
    await demo_signal_generation()
    await demo_status_reporting()
    await demo_full_list()
    await demo_quick_start()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nThe MEGA Integration system is ready for production use.")
    print("Run 'RUN_MEGA_INTEGRATION.bat' to start the full system.")
    print("=" * 70)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for demo
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run demos
    asyncio.run(main())
