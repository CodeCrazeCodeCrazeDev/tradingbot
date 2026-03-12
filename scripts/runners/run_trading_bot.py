#!/usr/bin/env python3
"""
AlphaAlgo Trading Bot - Unified Entry Point
============================================

This is the MAIN entry point for the entire trading bot system.
It provides multiple ways to run the bot:

1. MEGA Integration (recommended) - All 150+ modules unified
2. Ultimate Integration - Full system with all features
3. Master Trading System - 100% complete trading pipeline
4. Standard Main - Original trading bot

Usage:
    python run_trading_bot.py                    # Interactive menu
    python run_trading_bot.py --mega             # Run MEGA integration
    python run_trading_bot.py --ultimate         # Run Ultimate integration
    python run_trading_bot.py --master           # Run Master trading system
    python run_trading_bot.py --standard         # Run standard main.py
    python run_trading_bot.py --mode paper       # Specify mode
    python run_trading_bot.py --symbols BTCUSDT ETHUSDT  # Specify symbols

Author: AlphaAlgo Trading System
Version: 2.0.0
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging(level: str = 'INFO'):
    """Setup logging configuration"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('AlphaAlgo')


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print("""
       AAAAA  L      PPPP   H   H  AAAAA  AAAAA  L       GGGG   OOO  
      A   A  L      P   P  H   H  A   A  A   A  L      G      O   O 
      AAAAA  L      PPPP   HHHHH  AAAAA  AAAAA  L      G  GG  O   O 
      A   A  L      P      H   H  A   A  A   A  L      G   G  O   O 
      A   A  LLLLL  P      H   H  A   A  A   A  LLLLL   GGGG   OOO  
    """)
    print("                    ADVANCED ALGORITHMIC TRADING SYSTEM")
    print("                         150+ Modules | 300+ Features")
    print("=" * 70)


def interactive_menu():
    """Show interactive menu"""
    print("\nSelect trading system to run:")
    print()
    print("  [1] MEGA Integration (Recommended)")
    print("      - All 150+ modules unified")
    print("      - Complete trading pipeline")
    print("      - Maximum features")
    print()
    print("  [2] Ultimate Integration")
    print("      - Full system with all features")
    print("      - 6-layer architecture")
    print()
    print("  [3] Master Trading System")
    print("      - 100% complete trading pipeline")
    print("      - Production-ready")
    print()
    print("  [4] Standard Main")
    print("      - Original trading bot")
    print("      - Basic features")
    print()
    print("  [5] Check System Status")
    print("  [6] Run Demo")
    print("  [7] Exit")
    print()
    
    choice = input("Enter choice (1-7): ").strip()
    return choice


async def run_mega_integration(args):
    """Run MEGA Integration system"""
    from trading_bot.mega_integration import MegaIntegration, MegaConfig, SystemMode
    
    config = MegaConfig(
        mode=SystemMode(args.mode),
        symbols=args.symbols,
        initial_capital=args.capital,
        enable_quantum=args.quantum,
        enable_blockchain=args.blockchain,
        enable_sentiment=True,
        enable_alternative_data=True,
        enable_deepchart=True,
        enable_systems_ai=True
    )
    
    system = MegaIntegration(config)
    await system.initialize()
    await system.start()


async def run_ultimate_integration(args):
    """Run Ultimate Integration system"""
    from trading_bot.ultimate_integration import (
        UltimateIntegration, IntegrationConfig, IntegrationMode
    )
    
    config = IntegrationConfig(
        mode=IntegrationMode(args.mode.upper()),
        symbols=args.symbols,
        initial_capital=args.capital,
        enable_quantum=args.quantum,
        enable_blockchain=args.blockchain
    )
    
    system = UltimateIntegration(config)
    await system.initialize()
    await system.start()


async def run_master_trading(args):
    """Run Master Trading System"""
    from trading_bot.master_integration import MasterTradingSystem
    
    system = MasterTradingSystem({
        'mode': args.mode,
        'symbols': args.symbols,
        'capital': args.capital
    })
    
    print("\nMaster Trading System initialized")
    print(f"Status: {system.get_system_status()}")
    
    # Simple trading loop
    while True:
        try:
            for symbol in args.symbols:
                signal = {
                    'signal_id': f'SIG_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    'symbol': symbol,
                    'direction': 'BUY',
                    'confidence': 0.7,
                    'price': 0,
                    'prices': [],
                    'data': None,
                    'portfolio': {'capital': args.capital, 'value': args.capital, 'drawdown': 0},
                    'market_state': {'regime': 'normal', 'volatility': 0.01},
                    'order_type': 'MARKET',
                    'volatility': 0.01,
                    'token': 'demo',
                    'client_id': 'demo',
                    'venues': ['VENUE_A']
                }
                
                result = await system.execute_complete_trade(signal)
                print(f"Trade result for {symbol}: {result['status']}")
            
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            print("\nShutdown requested")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)


async def run_standard_main(args):
    """Run standard main.py"""
    from trading_bot.main import TradingBot, load_config
    
    config = load_config()
    config['trading']['mode'] = args.mode
    config['trading']['symbols'] = args.symbols
    
    bot = TradingBot(config)
    await bot.initialize()
    await bot.start()


def check_system_status():
    """Check and display system status"""
    print("\n" + "=" * 70)
    print("SYSTEM STATUS CHECK")
    print("=" * 70)
    
    # Check dependencies
    print("\n[1] Checking Dependencies...")
    try:
        from trading_bot.safe_imports import print_dependency_status
        print_dependency_status()
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check MEGA integration
    print("\n[2] Checking MEGA Integration...")
    try:
        from trading_bot.mega_integration import create_mega_system
        system = create_mega_system()
        print(f"  Health: {system.health.value}")
        print(f"  Active Modules: {len(system.active_modules)}")
        print(f"  Failed Modules: {len(system.failed_modules)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check Ultimate integration
    print("\n[3] Checking Ultimate Integration...")
    try:
        from trading_bot.ultimate_integration import create_ultimate_system
        system = create_ultimate_system()
        print(f"  Health: {system.health.value}")
        print(f"  Active Modules: {len(system.active_modules)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check Master Trading
    print("\n[4] Checking Master Trading System...")
    try:
        system = MasterTradingSystem()
        status = system.get_system_status()
        print(f"  Status: {status['status']}")
        print(f"  Overall: {status['OVERALL']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "=" * 70)


def run_demo():
    """Run demo script"""
    print("\nRunning MEGA Integration Demo...")
    try:
        import subprocess
        subprocess.run([sys.executable, 'examples/mega_integration_demo.py'], 
                      cwd=str(project_root))
    except Exception as e:
        print(f"Error running demo: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AlphaAlgo Trading Bot - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_trading_bot.py                    # Interactive menu
  python run_trading_bot.py --mega             # Run MEGA integration
  python run_trading_bot.py --ultimate         # Run Ultimate integration
  python run_trading_bot.py --master           # Run Master trading system
  python run_trading_bot.py --mode paper       # Paper trading mode
  python run_trading_bot.py --symbols BTCUSDT ETHUSDT
        """
    )
    
    # System selection
    parser.add_argument('--mega', action='store_true', 
                        help='Run MEGA Integration (recommended)')
    parser.add_argument('--ultimate', action='store_true',
                        help='Run Ultimate Integration')
    parser.add_argument('--master', action='store_true',
                        help='Run Master Trading System')
    parser.add_argument('--standard', action='store_true',
                        help='Run standard main.py')
    
    # Trading parameters
    parser.add_argument('--mode', choices=['paper', 'live', 'backtest', 'simulation'],
                        default='paper', help='Trading mode')
    parser.add_argument('--symbols', nargs='+', 
                        default=['BTCUSDT', 'ETHUSDT'],
                        help='Trading symbols')
    parser.add_argument('--capital', type=float, default=100000.0,
                        help='Initial capital')
    
    # Features
    parser.add_argument('--quantum', action='store_true',
                        help='Enable quantum computing')
    parser.add_argument('--blockchain', action='store_true',
                        help='Enable blockchain/DeFi')
    
    # Other
    parser.add_argument('--log-level', default='INFO',
                        help='Logging level')
    parser.add_argument('--status', action='store_true',
                        help='Check system status')
    parser.add_argument('--demo', action='store_true',
                        help='Run demo')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Handle special commands
    if args.status:
        check_system_status()
        return
    
    if args.demo:
        run_demo()
        return
    
    # Determine which system to run
    if args.mega:
        system_choice = '1'
    elif args.ultimate:
        system_choice = '2'
    elif args.master:
        system_choice = '3'
    elif args.standard:
        system_choice = '4'
    else:
        # Interactive menu
        system_choice = interactive_menu()
    
    # Run selected system
    try:
        if system_choice == '1':
            print("\nStarting MEGA Integration...")
            asyncio.run(run_mega_integration(args))
        elif system_choice == '2':
            print("\nStarting Ultimate Integration...")
            asyncio.run(run_ultimate_integration(args))
        elif system_choice == '3':
            print("\nStarting Master Trading System...")
            asyncio.run(run_master_trading(args))
        elif system_choice == '4':
            print("\nStarting Standard Main...")
            asyncio.run(run_standard_main(args))
        elif system_choice == '5':
            check_system_status()
        elif system_choice == '6':
            run_demo()
        elif system_choice == '7':
            print("\nGoodbye!")
        else:
            print("\nInvalid choice")
            
    except KeyboardInterrupt:
        print("\n\nShutdown requested. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
