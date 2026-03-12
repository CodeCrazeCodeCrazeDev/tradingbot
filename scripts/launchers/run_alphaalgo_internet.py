"""
AlphaAlgo Internet-Empowered Trading System
Quick Start Launcher
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.internet_access import AlphaAlgoOrchestrator


def setup_logging():
    """Configure logging for the system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('alphaalgo_internet.log')
        ]
    )


async def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🌐 ALPHAALGO INTERNET-EMPOWERED TRADING SYSTEM")
    print("=" * 80)
    print("\nInitializing autonomous trading system...")
    print("Press Ctrl+C to stop\n")
    
    # Setup logging
    setup_logging()
    
    # Create orchestrator
    orchestrator = AlphaAlgoOrchestrator()
    
    try:
        # Start autonomous operation
        await orchestrator.start_autonomous_operation()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Shutdown signal received...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.exception("System error")
    
    finally:
        # Graceful shutdown
        print("\n🛑 Stopping AlphaAlgo system...")
        await orchestrator.stop()
        
        # Save final status
        orchestrator.save_status_report('alphaalgo_final_status.json')
        
        print("✅ System stopped gracefully")
        print(f"📊 Final status saved to: alphaalgo_final_status.json")
        print(f"📝 Logs saved to: alphaalgo_internet.log\n")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
