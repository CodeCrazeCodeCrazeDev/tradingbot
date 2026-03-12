#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RUN UNIFIED AI BRAIN                                       ║
║                                                                                ║
║  The ONE entry point that activates ALL 2900+ files as a single AI system    ║
║                                                                                ║
║  Usage:                                                                        ║
║    python run_unified_brain.py                    # Interactive mode           ║
║    python run_unified_brain.py --mode paper       # Paper trading             ║
║    python run_unified_brain.py --mode live        # Live trading (careful!)   ║
║    python run_unified_brain.py --symbols BTCUSDT EURUSD                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_dir = Path("brain_logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"brain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def print_banner():
    """Print the startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                          ║
║   ██╗   ██╗███╗   ██╗██╗███████╗██╗███████╗██████╗      █████╗ ██╗    ██████╗ ██████╗    ║
║   ██║   ██║████╗  ██║██║██╔════╝██║██╔════╝██╔══██╗    ██╔══██╗██║    ██╔══██╗██╔══██╗   ║
║   ██║   ██║██╔██╗ ██║██║█████╗  ██║█████╗  ██║  ██║    ███████║██║    ██████╔╝██████╔╝   ║
║   ██║   ██║██║╚██╗██║██║██╔══╝  ██║██╔══╝  ██║  ██║    ██╔══██║██║    ██╔══██╗██╔══██╗   ║
║   ╚██████╔╝██║ ╚████║██║██║     ██║███████╗██████╔╝    ██║  ██║██║    ██████╔╝██║  ██║   ║
║    ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚══════╝╚═════╝     ╚═╝  ╚═╝╚═╝    ╚═════╝ ╚═╝  ╚═╝   ║
║                                                                                          ║
║                    THE ONE AI BRAIN - 2900+ Files Working As One                         ║
║                                                                                          ║
║   "Many modules, ONE mind. Many features, ONE purpose. Many files, ONE AI."              ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """Print interactive menu"""
    menu = """
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED AI BRAIN MENU                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Awaken Brain (Initialize all subsystems)                    │
│  2. Run Paper Trading                                           │
│  3. Run Backtest Mode                                           │
│  4. Show Brain Status                                           │
│  5. Show Loaded Subsystems                                      │
│  6. Generate Single Thought (Test)                              │
│  7. Emergency Stop                                              │
│  8. Shutdown & Exit                                             │
├─────────────────────────────────────────────────────────────────┤
│  0. Quick Start (Awaken + Paper Trading)                        │
└─────────────────────────────────────────────────────────────────┘
    """
    print(menu)


async def interactive_mode(brain):
    """Run in interactive mode"""
    from trading_bot.unified_ai_brain import BrainState
    
    while True:
        print_menu()
        choice = input("\nEnter choice (0-8): ").strip()
        
        if choice == '0':
            # Quick start
            print("\n[QUICK START]")
            if brain.state == BrainState.DORMANT:
                print("Awakening brain...")
                await brain.awaken()
            
            if brain.state == BrainState.CONSCIOUS:
                print("Starting paper trading...")
                print("Press Ctrl+C to stop\n")
                try:
                    await brain.run()
                except KeyboardInterrupt:
                    print("\nStopped by user")
        
        elif choice == '1':
            # Awaken
            print("\n[AWAKENING BRAIN]")
            if brain.state == BrainState.DORMANT:
                await brain.awaken()
            else:
                print(f"Brain already in state: {brain.state.value}")
        
        elif choice == '2':
            # Paper trading
            print("\n[PAPER TRADING]")
            if brain.state != BrainState.CONSCIOUS:
                print("Brain must be conscious first. Awakening...")
                await brain.awaken()
            
            if brain.state == BrainState.CONSCIOUS:
                print("Starting paper trading... Press Ctrl+C to stop\n")
                try:
                    await brain.run()
                except KeyboardInterrupt:
                    print("\nStopped by user")
        
        elif choice == '3':
            # Backtest
            print("\n[BACKTEST MODE]")
            print("Backtest mode not yet implemented in this version.")
            print("Use the existing backtesting module directly.")
        
        elif choice == '4':
            # Status
            print("\n[BRAIN STATUS]")
            status = brain.get_status()
            print(f"  State: {status.state.value}")
            print(f"  Uptime: {status.uptime_seconds:.1f} seconds")
            print(f"  Subsystems: {status.loaded_subsystems}/{status.total_subsystems} loaded")
            print(f"  Failed: {status.failed_subsystems}")
            print(f"  Thoughts: {status.thoughts_generated}")
            print(f"  Trades: {status.trades_executed}")
            print(f"  Capital: ${status.capital:,.2f}")
            print(f"  PnL: ${status.pnl:,.2f} ({status.pnl_percent:.2f}%)")
            print(f"  Health: {status.health_score:.1%}")
        
        elif choice == '5':
            # Subsystems
            print("\n[LOADED SUBSYSTEMS]")
            for name in sorted(brain.loaded_subsystems):
                ss = brain.subsystems.get(name)
                if ss:
                    print(f"  ✓ {name} ({ss.category.value})")
            
            if brain.failed_subsystems:
                print("\n[FAILED SUBSYSTEMS]")
                for name in sorted(brain.failed_subsystems):
                    ss = brain.subsystems.get(name)
                    if ss:
                        print(f"  ✗ {name}: {ss.error}")
        
        elif choice == '6':
            # Test thought
            print("\n[GENERATE TEST THOUGHT]")
            if brain.state != BrainState.CONSCIOUS:
                print("Brain must be conscious first.")
                continue
            
            symbol = input("Enter symbol (default: BTCUSDT): ").strip() or "BTCUSDT"
            
            market_data = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'close': 50000.0,
                'high': 51000.0,
                'low': 49000.0,
                'volume': 1000000
            }
            
            print(f"Thinking about {symbol}...")
            thought = await brain.think(symbol, market_data)
            
            if thought:
                print(f"\n  Thought ID: {thought.thought_id}")
                print(f"  Action: {thought.action}")
                print(f"  Confidence: {thought.confidence:.2%}")
                print(f"  Reasoning: {thought.reasoning}")
                print(f"  Approved: {thought.approved}")
            else:
                print("  No actionable thought generated (HOLD)")
        
        elif choice == '7':
            # Emergency stop
            print("\n[EMERGENCY STOP]")
            confirm = input("Are you sure? (yes/no): ").strip().lower()
            if confirm == 'yes':
                await brain.emergency_stop("User requested emergency stop")
                print("Emergency stop activated!")
        
        elif choice == '8':
            # Shutdown
            print("\n[SHUTDOWN]")
            await brain.shutdown()
            print("Brain shutdown complete. Goodbye!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified AI Brain - The ONE Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_unified_brain.py                     # Interactive mode
  python run_unified_brain.py --mode paper        # Paper trading
  python run_unified_brain.py --symbols BTCUSDT EURUSD --capital 50000
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['paper', 'live', 'backtest', 'simulation'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    
    parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        default=['BTCUSDT', 'EURUSD'],
        help='Symbols to trade (default: BTCUSDT EURUSD)'
    )
    
    parser.add_argument(
        '--capital', '-c',
        type=float,
        default=100000.0,
        help='Initial capital (default: 100000)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--quick-start', '-q',
        action='store_true',
        help='Quick start: awaken and run immediately'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Import brain
    try:
        from trading_bot.unified_ai_brain import UnifiedAIBrain, BrainConfig, BrainState
    except ImportError as e:
        logger.error(f"Failed to import UnifiedAIBrain: {e}")
        logger.error("Make sure you're running from the trading bot directory")
        sys.exit(1)
    
    # Create config
    config = BrainConfig(
        mode=args.mode,
        symbols=args.symbols,
        initial_capital=args.capital
    )
    
    # Create brain
    logger.info("Creating Unified AI Brain...")
    brain = UnifiedAIBrain(config)
    
    try:
        if args.interactive or (not args.quick_start and len(sys.argv) == 1):
            # Interactive mode
            await interactive_mode(brain)
        
        elif args.quick_start:
            # Quick start
            logger.info("Quick starting brain...")
            await brain.awaken()
            
            if brain.state == BrainState.CONSCIOUS:
                logger.info("Brain is conscious. Starting trading loop...")
                logger.info("Press Ctrl+C to stop")
                await brain.run(args.symbols)
        
        else:
            # Direct mode
            logger.info(f"Starting in {args.mode} mode...")
            await brain.awaken()
            
            if brain.state == BrainState.CONSCIOUS:
                logger.info("Brain is conscious. Starting trading loop...")
                logger.info("Press Ctrl+C to stop")
                await brain.run(args.symbols)
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if brain.state not in [BrainState.SHUTDOWN, BrainState.DORMANT]:
            await brain.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
