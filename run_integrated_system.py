#!/usr/bin/env python
"""
Quick Start Script for Integrated Trading Bot System
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot import (
    MasterOrchestrator,
    OrchestratorConfig,
    initialize_orchestrator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_system(args):
    """Run the integrated trading system."""
    print("🚀 Starting Integrated Trading Bot System...")
    
    # Create configuration
    config = OrchestratorConfig(
        mode=args.mode,
        symbols=args.symbols.split(',') if args.symbols else ['EURUSD'],
        timeframes=args.timeframes.split(',') if args.timeframes else ['M5', 'M15'],
        enable_ai_features=args.enable_ai,
        enable_ml_features=args.enable_ml,
        enable_evolution_features=args.enable_evolution,
        enable_sentient_features=args.enable_sentient,
        health_check_interval=args.health_check_interval,
        auto_start=args.auto_start
    )
    
    # Initialize and start orchestrator
    orchestrator = await initialize_orchestrator(config)
    
    if not orchestrator.initialized:
        print("❌ Failed to initialize system")
        return 1
    
    print("✅ System initialized successfully")
    
    # Start system
    if args.auto_start:
        success = await orchestrator.start()
        if not success:
            print("❌ Failed to start system")
            return 1
        print("✅ System started successfully")
    
    # Show status
    status = orchestrator.get_status()
    print(f"\n📊 System Status:")
    print(f"   Mode: {status['mode']}")
    print(f"   Modules: {status['metrics']['modules_loaded']}")
    print(f"   Services: {status['metrics']['services_active']}")
    
    # Run until interrupted
    if args.interactive:
        print("\n🎮 Interactive Mode - Press Ctrl+C to stop")
        print("Commands: status, start, stop, quit")
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                
                if cmd == 'quit' or cmd == 'q':
                    break
                elif cmd == 'status':
                    status = orchestrator.get_status()
                    print(f"Running: {status['running']}")
                    print(f"Services: {status['metrics']['services_active']}")
                elif cmd == 'start' and not orchestrator.running:
                    await orchestrator.start()
                    print("✅ System started")
                elif cmd == 'stop' and orchestrator.running:
                    await orchestrator.stop()
                    print("⏹️ System stopped")
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
    else:
        print("\n⏳ Running... Press Ctrl+C to stop")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
    
    # Shutdown
    print("\n🛑 Shutting down...")
    await orchestrator.shutdown()
    print("✅ Shutdown complete")
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Integrated Trading Bot System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integrated_system.py --mode paper
  python run_integrated_system.py --mode paper --symbols EURUSD,GBPUSD --interactive
  python run_integrated_system.py --enable-ai --enable-ml --health-check 10
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['paper', 'simulation', 'live'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        help='Trading symbols (comma-separated)'
    )
    
    parser.add_argument(
        '--timeframes',
        type=str,
        help='Timeframes (comma-separated)'
    )
    
    parser.add_argument(
        '--enable-ai',
        action='store_true',
        help='Enable AI features'
    )
    
    parser.add_argument(
        '--enable-ml',
        action='store_true',
        help='Enable ML features'
    )
    
    parser.add_argument(
        '--enable-evolution',
        action='store_true',
        help='Enable evolution features'
    )
    
    parser.add_argument(
        '--enable-sentient',
        action='store_true',
        help='Enable sentient features (experimental)'
    )
    
    parser.add_argument(
        '--health-check',
        type=int,
        dest='health_check_interval',
        default=30,
        help='Health check interval in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--auto-start',
        action='store_true',
        help='Auto-start trading system'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo instead of full system'
    )
    
    args = parser.parse_args()
    
    # Run demo if requested
    if args.demo:
        print("🎬 Running Module Integration Demo...")
        from examples.module_integration_demo import main as demo_main
        return asyncio.run(demo_main())
    
    # Run main system
    try:
        return asyncio.run(run_system(args))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        print(f"\n❌ System error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
