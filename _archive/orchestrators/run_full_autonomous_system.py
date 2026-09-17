"""
Full Autonomous System Launcher
Launches the complete trading bot with autonomous superintelligence.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from trading_bot.core_agent_system import IntegratedAgentSystem

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
        'total_capital': 100000.0,
        'max_agents': 50,
        'min_agents': 10,
        'safety_threshold': 0.7,
        'max_experiments': 10,
        'scan_interval': 60,
    }
    
    system = IntegratedAgentSystem(config)
    
    def signal_handler(sig, frame):
        logger.info("\nShutdown signal received")
        asyncio.create_task(system.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.initialize()
        asyncio.create_task(system.start())
        
        logger.info("\n🚀 FULL UNIFIED AUTONOMOUS SYSTEM IS NOW OPERATIONAL 🚀\n")
        logger.info("The system will:")
        logger.info("  • Trade using Integrated Agent System")
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
        
        while system.running:
            await asyncio.sleep(60)
            
            status = system.get_comprehensive_status()
            logger.info("System Status - Agents: %d, Tools: %d, Iteration: %d",
                      status['agents']['total_agents'],
                      status['tools']['total_tools'],
                      status['self_play']['iteration'])
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await system.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
