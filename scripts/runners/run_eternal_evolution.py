#!/usr/bin/env python3
"""
Eternal Evolution Trading Bot - Main Runner
============================================

A trading bot that evolves EVERYTHING while remaining a trading bot at its core.

EVOLVES:
- Risk Management
- Architecture & Stability
- Data Quality
- Level 2 Data
- Alternative Data
- Security

NEVER CHANGES:
- Core identity as a TRADING BOT
- Purpose: Generate profitable trades
- Ethical boundaries

Usage:
    python run_eternal_evolution.py [options]

Options:
    --mode          Trading mode: paper, live, backtest (default: paper)
    --symbols       Comma-separated symbols (default: BTCUSDT,ETHUSDT)
    --evolve-now    Run evolution cycle immediately
    --status        Show current evolution status
    --demo          Run demo mode
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.eternal_evolution import EternalEvolutionOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'eternal_evolution_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print the eternal evolution banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗████████╗███████╗██████╗ ███╗   ██╗ █████╗ ██╗                     ║
║   ██╔════╝╚══██╔══╝██╔════╝██╔══██╗████╗  ██║██╔══██╗██║                     ║
║   █████╗     ██║   █████╗  ██████╔╝██╔██╗ ██║███████║██║                     ║
║   ██╔══╝     ██║   ██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║                     ║
║   ███████╗   ██║   ███████╗██║  ██║██║ ╚████║██║  ██║███████╗                ║
║   ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝                ║
║                                                                              ║
║   ███████╗██╗   ██╗ ██████╗ ██╗     ██╗   ██╗████████╗██╗ ██████╗ ███╗   ██╗ ║
║   ██╔════╝██║   ██║██╔═══██╗██║     ██║   ██║╚══██╔══╝██║██╔═══██╗████╗  ██║ ║
║   █████╗  ██║   ██║██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██╔██╗ ██║ ║
║   ██╔══╝  ╚██╗ ██╔╝██║   ██║██║     ██║   ██║   ██║   ██║██║   ██║██║╚██╗██║ ║
║   ███████╗ ╚████╔╝ ╚██████╔╝███████╗╚██████╔╝   ██║   ██║╚██████╔╝██║ ╚████║ ║
║   ╚══════╝  ╚═══╝   ╚═════╝ ╚══════╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                                              ║
║                    TRADING BOT - FOREVER EVOLVING                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_demo():
    """Run a demo of the eternal evolution system"""
    print_banner()
    print("\n" + "=" * 80)
    print("ETERNAL EVOLUTION DEMO")
    print("=" * 80 + "\n")
    
    # Create the system
    config = {
        'evolution_interval_hours': 1,  # Evolve every hour for demo
        'auto_evolve': False,  # Manual evolution for demo
        'risk': {'learning_rate': 0.1},
        'architecture': {},
        'data': {},
        'security': {}
    }
    
    system = EternalEvolutionOrchestrator(config)
    
    # Show identity declaration
    print(system.immutable_core.declare_identity())
    
    # Show purpose declaration
    print(system.declare_purpose())
    
    # Run an evolution cycle
    print("\n" + "=" * 80)
    print("RUNNING EVOLUTION CYCLE")
    print("=" * 80 + "\n")
    
    cycle = await system.evolve_all()
    
    print(f"\nEvolution Cycle Complete!")
    print(f"  Cycle ID: {cycle.cycle_id}")
    print(f"  Dimensions Evolved: {cycle.dimensions_evolved}")
    print(f"  Changes Made: {len(cycle.changes_made)}")
    
    # Generate a sample signal
    print("\n" + "=" * 80)
    print("GENERATING TRADING SIGNAL")
    print("=" * 80 + "\n")
    
    sample_market_data = {
        'symbol': 'BTCUSDT',
        'price': 45000,
        'close': 45000,
        'open': 44500,
        'high': 45500,
        'low': 44000,
        'volume': 1000000,
        'volatility': 0.03,
        'atr': 1350,
        'trend': 'up',
        'account_balance': 10000,
        'timestamp': datetime.now().isoformat()
    }
    
    signal = await system.generate_signal('BTCUSDT', sample_market_data)
    
    print(f"Signal Generated:")
    print(f"  Signal ID: {signal.signal_id}")
    print(f"  Symbol: {signal.symbol}")
    print(f"  Direction: {signal.direction}")
    print(f"  Confidence: {signal.confidence:.2%}")
    print(f"  Entry Price: ${signal.entry_price:,.2f}")
    print(f"  Stop Loss: ${signal.stop_loss:,.2f}")
    print(f"  Take Profit: ${signal.take_profit:,.2f}")
    print(f"  Position Size: {signal.position_size:.4f}")
    print(f"  Risk Score: {signal.risk_score:.2%}")
    print(f"  Data Quality: {signal.data_quality_score:.2%}")
    print(f"  Security Validated: {signal.security_validated}")
    print(f"  Reasoning: {signal.reasoning}")
    
    # Show evolution summary
    print("\n" + "=" * 80)
    print("EVOLUTION SUMMARY")
    print("=" * 80 + "\n")
    
    summary = system.get_evolution_summary()
    
    print("Identity:")
    print(f"  Name: {summary['identity']['name']}")
    print(f"  Is Trading Bot: {summary['identity']['is_trading_bot']}")
    
    print("\nEvolution Stats:")
    print(f"  Total Cycles: {summary['evolution_stats']['total_cycles']}")
    print(f"  Total Changes: {summary['evolution_stats']['total_changes']}")
    
    print("\nDimension Stats:")
    for dim, stats in summary['dimension_stats'].items():
        print(f"\n  {dim.upper()}:")
        for key, value in list(stats.items())[:5]:
            print(f"    {key}: {value}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nThe bot has demonstrated:")
    print("  ✓ Immutable trading identity")
    print("  ✓ Risk management evolution")
    print("  ✓ Architecture evolution")
    print("  ✓ Data quality evolution")
    print("  ✓ Security evolution")
    print("  ✓ Signal generation with all evolved systems")
    print("\nIt remains a TRADING BOT while evolving everything else!")


async def run_status(system: EternalEvolutionOrchestrator):
    """Show current evolution status"""
    print_banner()
    print(system.declare_purpose())
    
    history = system.get_evolution_history(10)
    
    print("\nRecent Evolution History:")
    print("-" * 60)
    for cycle in history:
        print(f"  {cycle['timestamp'][:19]} | {cycle['cycle_id']}")
        print(f"    Dimensions: {', '.join(cycle['dimensions'])}")
        print(f"    Changes: {cycle['changes_count']}")
        print()


async def run_trading_loop(system: EternalEvolutionOrchestrator, symbols: list, mode: str):
    """Run the main trading loop"""
    print_banner()
    print(f"\nStarting Eternal Evolution Trading Bot")
    print(f"Mode: {mode}")
    print(f"Symbols: {symbols}")
    print("-" * 60)
    
    await system.start()
    
    print("\nBot is running. Press Ctrl+C to stop.")
    print("Evolution will occur automatically based on configured interval.")
    
    try:
        while True:
            for symbol in symbols:
                # In a real implementation, this would fetch real market data
                sample_data = {
                    'symbol': symbol,
                    'price': 45000 if 'BTC' in symbol else 3000,
                    'close': 45000 if 'BTC' in symbol else 3000,
                    'volatility': 0.03,
                    'atr': 1350 if 'BTC' in symbol else 90,
                    'trend': 'neutral',
                    'account_balance': 10000,
                    'timestamp': datetime.now().isoformat()
                }
                
                signal = await system.generate_signal(symbol, sample_data)
                
                if signal.direction != 'hold':
                    logger.info(
                        "Signal: %s %s @ %s (conf: %.2f%%, risk: %.2f%%)",
                        symbol, signal.direction, signal.entry_price,
                        signal.confidence * 100, signal.risk_score * 100
                    )
            
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        await system.stop()
        print("Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description='Eternal Evolution Trading Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_eternal_evolution.py --demo
    python run_eternal_evolution.py --status
    python run_eternal_evolution.py --mode paper --symbols BTCUSDT,ETHUSDT
    python run_eternal_evolution.py --evolve-now
        """
    )
    
    parser.add_argument('--mode', choices=['paper', 'live', 'backtest'],
                       default='paper', help='Trading mode')
    parser.add_argument('--symbols', type=str, default='BTCUSDT,ETHUSDT',
                       help='Comma-separated symbols to trade')
    parser.add_argument('--evolve-now', action='store_true',
                       help='Run evolution cycle immediately')
    parser.add_argument('--status', action='store_true',
                       help='Show current evolution status')
    parser.add_argument('--demo', action='store_true',
                       help='Run demo mode')
    parser.add_argument('--evolution-interval', type=int, default=6,
                       help='Hours between evolution cycles')
    
    args = parser.parse_args()
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Create config
    config = {
        'evolution_interval_hours': args.evolution_interval,
        'auto_evolve': True,
        'mode': args.mode,
        'risk': {},
        'architecture': {},
        'data': {},
        'security': {}
    }
    
    if args.demo:
        asyncio.run(run_demo())
    elif args.status:
        system = EternalEvolutionOrchestrator(config)
        asyncio.run(run_status(system))
    elif args.evolve_now:
        system = EternalEvolutionOrchestrator(config)
        print_banner()
        print("\nRunning evolution cycle...")
        asyncio.run(system.evolve_all())
        print("\nEvolution complete!")
    else:
        system = EternalEvolutionOrchestrator(config)
        asyncio.run(run_trading_loop(system, symbols, args.mode))


if __name__ == '__main__':
    main()
