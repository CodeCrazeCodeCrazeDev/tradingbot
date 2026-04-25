"""
Autonomous Superintelligence Launcher
Main entry point for the autonomous AI system.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.autonomous_superintelligence.superintelligence_orchestrator import (
    AutonomousSuperintelligence
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('autonomous_superintelligence.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("AUTONOMOUS SUPERINTELLIGENCE SYSTEM")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Capabilities:")
    logger.info("  ✓ Self-managing operations")
    logger.info("  ✓ Multi-agent coordination")
    logger.info("  ✓ Self-improvement and optimization")
    logger.info("  ✓ Code self-modification")
    logger.info("  ✓ Scientific research and discovery")
    logger.info("  ✓ Agent spawning and lifecycle management")
    logger.info("  ✓ Global opportunity detection")
    logger.info("  ✓ Autonomous capital deployment")
    logger.info("  ✓ Continuous experimentation")
    logger.info("  ✓ Model evolution and deployment")
    logger.info("")
    logger.info("=" * 80)
    
    config = {
        'total_capital': 100000.0,
        'max_agents': 100,
        'min_agents': 10,
        'safety_enabled': True,
        'max_concurrent_experiments': 10,
        'scan_interval': 60,
    }
    
    superintelligence = AutonomousSuperintelligence(config)
    
    def signal_handler(sig, frame):
        logger.info("\nShutdown signal received")
        asyncio.create_task(superintelligence.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await superintelligence.initialize()
        
        logger.info("\n🚀 SYSTEM IS NOW FULLY AUTONOMOUS AND SELF-MANAGING 🚀\n")
        
        await superintelligence.start()
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await superintelligence.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
