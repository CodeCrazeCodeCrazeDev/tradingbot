"""
AlphaAlgo V1 to V2 Migration Script

This script helps migrate from the legacy V1 architecture to the new V2 architecture.

Usage:
    python migrate_to_v2.py --check     # Check migration readiness
    python migrate_to_v2.py --parallel  # Run V2 alongside V1
    python migrate_to_v2.py --migrate   # Full migration (backup first!)
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_migration_readiness():
    """Check if system is ready for migration"""
    print("\n" + "=" * 60)
    print("AlphaAlgo V2 Migration Readiness Check")
    print("=" * 60 + "\n")
    
    checks = []
    
    # Check V2 package exists
    v2_path = Path("trading_bot/alphaalgo_v2")
    if v2_path.exists():
        checks.append(("V2 package exists", True))
    else:
        checks.append(("V2 package exists", False))
    
    # Check core modules
    core_modules = [
        "trading_bot/alphaalgo_v2/core/__init__.py",
        "trading_bot/alphaalgo_v2/core/interfaces.py",
        "trading_bot/alphaalgo_v2/core/types.py",
        "trading_bot/alphaalgo_v2/core/constants.py",
        "trading_bot/alphaalgo_v2/core/exceptions.py",
    ]
    
    all_core = all(Path(m).exists() for m in core_modules)
    checks.append(("Core modules present", all_core))
    
    # Check data layer
    data_modules = [
        "trading_bot/alphaalgo_v2/data/__init__.py",
        "trading_bot/alphaalgo_v2/data/pipeline.py",
    ]
    all_data = all(Path(m).exists() for m in data_modules)
    checks.append(("Data layer present", all_data))
    
    # Check models layer
    models_modules = [
        "trading_bot/alphaalgo_v2/models/__init__.py",
        "trading_bot/alphaalgo_v2/models/brain.py",
    ]
    all_models = all(Path(m).exists() for m in models_modules)
    checks.append(("Models layer present", all_models))
    
    # Check execution layer
    execution_modules = [
        "trading_bot/alphaalgo_v2/execution/__init__.py",
        "trading_bot/alphaalgo_v2/execution/engine.py",
    ]
    all_execution = all(Path(m).exists() for m in execution_modules)
    checks.append(("Execution layer present", all_execution))
    
    # Check risk engine
    risk_modules = [
        "trading_bot/alphaalgo_v2/risk_engine/__init__.py",
        "trading_bot/alphaalgo_v2/risk_engine/engine.py",
    ]
    all_risk = all(Path(m).exists() for m in risk_modules)
    checks.append(("Risk engine present", all_risk))
    
    # Check evolution engine
    evolution_modules = [
        "trading_bot/alphaalgo_v2/evolution/__init__.py",
        "trading_bot/alphaalgo_v2/evolution/orchestrator.py",
    ]
    all_evolution = all(Path(m).exists() for m in evolution_modules)
    checks.append(("Evolution engine present", all_evolution))
    
    # Check reward engine
    reward_modules = [
        "trading_bot/alphaalgo_v2/reward_engine/__init__.py",
        "trading_bot/alphaalgo_v2/reward_engine/immutable_rewards.py",
    ]
    all_reward = all(Path(m).exists() for m in reward_modules)
    checks.append(("Reward engine present", all_reward))
    
    # Check main orchestrator
    orchestrator_exists = Path("trading_bot/alphaalgo_v2/orchestrator.py").exists()
    checks.append(("Main orchestrator present", orchestrator_exists))
    
    # Check tests
    tests_exist = Path("trading_bot/alphaalgo_v2/tests").exists()
    checks.append(("Test suite present", tests_exist))
    
    # Print results
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset} {check_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("\033[92m✓ All checks passed! Ready for migration.\033[0m")
    else:
        print("\033[91m✗ Some checks failed. Please fix before migrating.\033[0m")
    
    return all_passed


async def run_parallel():
    """Run V2 alongside V1 for comparison"""
    print("\n" + "=" * 60)
    print("Running V2 in Parallel Mode")
    print("=" * 60 + "\n")
    
    try:
        from trading_bot.alphaalgo_v2 import quick_start
        
        # Start V2 system
        print("Starting AlphaAlgo V2...")
        system = await quick_start({
            "mode": "paper",
            "initial_balance": 10000,
        })
        
        print(f"V2 State: {system.state.value}")
        print(f"V2 Mode: {system.mode.value}")
        
        # Start trading
        print("\nStarting V2 paper trading...")
        await system.start_trading(["EURUSD", "GBPUSD"])
        
        print("V2 is now running in parallel with V1")
        print("Press Ctrl+C to stop\n")
        
        # Run for a while
        try:
            while True:
                status = system.get_status()
                print(f"\rV2 Status: {status['state']} | "
                      f"Signals: {status['session']['signals_generated']} | "
                      f"Executed: {status['session']['signals_executed']}", end="")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopping V2...")
        
        await system.stop_trading()
        await system.shutdown()
        
        print("V2 stopped successfully")
        
    except ImportError as e:
        print(f"Error importing V2: {e}")
        print("Make sure V2 is properly installed")
    except Exception as e:
        print(f"Error running V2: {e}")


def show_migration_plan():
    """Show the migration plan"""
    print("\n" + "=" * 60)
    print("AlphaAlgo V2 Migration Plan")
    print("=" * 60 + "\n")
    
    plan = """
PHASE 1: Parallel Operation (Current)
-------------------------------------
1. V2 runs alongside V1 in paper mode
2. Compare signals and performance
3. Validate V2 behavior matches expectations
4. Duration: 1-2 weeks

PHASE 2: Gradual Component Migration
------------------------------------
1. Replace V1 data sources with V2 data layer
2. Replace V1 signal generators with V2 models
3. Replace V1 risk manager with V2 risk engine
4. Replace V1 executor with V2 execution engine
5. Duration: 2-4 weeks

PHASE 3: Full Migration
-----------------------
1. Switch main entry point to V2 orchestrator
2. Deprecate V1 components
3. Archive V1 code
4. Duration: 1 week

PHASE 4: Cleanup
----------------
1. Remove deprecated V1 code
2. Update documentation
3. Update deployment scripts
4. Duration: 1 week

TOTAL ESTIMATED TIME: 5-8 weeks

ROLLBACK PLAN:
- V1 code remains intact during migration
- Can switch back to V1 at any time
- Database and state are compatible
"""
    print(plan)


def create_v2_entry_point():
    """Create a new entry point for V2"""
    content = '''"""
AlphaAlgo V2 Entry Point

This is the main entry point for the V2 trading system.
"""

from trading_bot.alphaalgo_v2 import quick_start, AlphaAlgoOrchestrator
from trading_bot.alphaalgo_v2.core.constants import TradingMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='AlphaAlgo V2 Trading System')
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], default='paper')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD'])
    parser.add_argument('--balance', type=float, default=10000)
    args = parser.parse_args()
    
    config = {
        'mode': args.mode,
        'initial_balance': args.balance,
    }
    
    logger.info(f"Starting AlphaAlgo V2 in {args.mode} mode")
    logger.info(f"Symbols: {args.symbols}")
    
    # Initialize system
    system = await quick_start(config)
    
    # Start trading
    await system.start_trading(args.symbols)
    
    logger.info("Trading started. Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    
    await system.stop_trading()
    await system.shutdown()
    
    logger.info("Shutdown complete")


if __name__ == '__main__':
    asyncio.run(main())
'''
    
    with open("main_v2.py", "w") as f:
        f.write(content)
    
    print("Created main_v2.py - V2 entry point")


def main():
    parser = argparse.ArgumentParser(description='AlphaAlgo V1 to V2 Migration')
    parser.add_argument('--check', action='store_true', help='Check migration readiness')
    parser.add_argument('--parallel', action='store_true', help='Run V2 alongside V1')
    parser.add_argument('--plan', action='store_true', help='Show migration plan')
    parser.add_argument('--create-entry', action='store_true', help='Create V2 entry point')
    
    args = parser.parse_args()
    
    if args.check:
        check_migration_readiness()
    elif args.parallel:
        asyncio.run(run_parallel())
    elif args.plan:
        show_migration_plan()
    elif args.create_entry:
        create_v2_entry_point()
    else:
        parser.print_help()
        print("\n\nQuick Start:")
        print("  1. python migrate_to_v2.py --check      # Check readiness")
        print("  2. python migrate_to_v2.py --plan       # View migration plan")
        print("  3. python migrate_to_v2.py --parallel   # Run V2 in parallel")
        print("  4. python migrate_to_v2.py --create-entry  # Create V2 entry point")


if __name__ == '__main__':
    main()
