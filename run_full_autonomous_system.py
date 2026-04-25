"""
Full Autonomous System Launcher
Launches the complete trading bot with autonomous superintelligence.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from master_orchestrator import MasterOrchestrator
from trading_bot.autonomous_superintelligence import AutonomousSuperintelligence

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('full_autonomous_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for full autonomous system."""
    logger.info("=" * 80)
    logger.info("FULL AUTONOMOUS TRADING SYSTEM")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Launching integrated system with:")
    logger.info("  ✓ Traditional Trading Bot (5 layers)")
    logger.info("  ✓ Autonomous Superintelligence")
    logger.info("  ✓ Self-improvement capabilities")
    logger.info("  ✓ Global opportunity detection")
    logger.info("  ✓ Continuous research and discovery")
    logger.info("")
    logger.info("=" * 80)
    
    config = {
        'enable_superintelligence': True,
        'si_capital': 100000.0,
        'si_max_agents': 50,
        'si_min_agents': 10,
        'si_safety': True,
        'si_max_experiments': 10,
        'si_scan_interval': 60,
    }
    
    orchestrator = MasterOrchestrator(config)
    
    def signal_handler(sig, frame):
        logger.info("\nShutdown signal received")
        orchestrator.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await orchestrator.start_all_async()
        
        orchestrator.print_status()
        
        logger.info("\n🚀 FULL AUTONOMOUS SYSTEM IS NOW OPERATIONAL 🚀\n")
        logger.info("The system will:")
        logger.info("  • Trade using traditional strategies")
        logger.info("  • Manage its own operations autonomously")
        logger.info("  • Discover new trading methods")
        logger.info("  • Detect global opportunities")
        logger.info("  • Deploy capital automatically")
        logger.info("  • Improve itself continuously")
        logger.info("  • Conduct scientific research")
        logger.info("  • Spawn and coordinate agents")
        logger.info("")
        logger.info("Monitor logs: full_autonomous_system.log")
        logger.info("Press Ctrl+C to shutdown gracefully")
        logger.info("")
        
        while orchestrator.running:
            await asyncio.sleep(60)
            
            if orchestrator.superintelligence:
                status = await orchestrator.superintelligence.get_comprehensive_status()
                logger.info("System Status - Autonomy: %.1f%%, Agents: %d, Discoveries: %d",
                          status['core']['autonomy_level'] * 100,
                          status['agents']['total_agents'],
                          status['research']['total_discoveries'])
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await orchestrator.stop_all_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
