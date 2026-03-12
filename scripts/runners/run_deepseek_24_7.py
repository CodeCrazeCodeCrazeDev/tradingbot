"""
DeepSeek AI Engineer - 24/7 Autonomous Runner
==============================================

This script starts the DeepSeek AI Engineer system to run 24/7 autonomously.

The system will:
- Continuously scan and understand the codebase
- Fix issues automatically without human approval
- Evolve strategies using genetic algorithms
- Research and integrate new algorithms
- Harden security
- Optimize performance
- Generate reports for human review

CRITICAL: The system will NEVER change the bot's purpose or reward system.

Usage:
    python run_deepseek_24_7.py [--mode MODE] [--single-cycle]

Options:
    --mode: Operating mode (full_autonomous, supervised, maintenance_only, evolution_only, research_only)
    --single-cycle: Run a single cycle instead of continuous operation
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.deepseek_ai_engineer import (
    DeepSeekOrchestrator,
    OrchestratorConfig,
    verify_purpose_integrity,
    quick_start,
)
from trading_bot.deepseek_ai_engineer.deepseek_orchestrator import OrchestratorMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'deepseek_engineer.log'),
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗ ███████╗███████╗██████╗ ███████╗███████╗███████╗██╗  ██╗         ║
║     ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝██║ ██╔╝         ║
║     ██║  ██║█████╗  █████╗  ██████╔╝███████╗█████╗  █████╗  █████╔╝          ║
║     ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ╚════██║██╔══╝  ██╔══╝  ██╔═██╗          ║
║     ██████╔╝███████╗███████╗██║     ███████║███████╗███████╗██║  ██╗         ║
║     ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝         ║
║                                                                              ║
║                    CHIEF AI ENGINEER SYSTEM                                  ║
║                    24/7 Autonomous Operation                                 ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Roles: Chief AI Engineer | Architect | Quant Researcher | Security Officer ║
║         Self-Evolution Engine | Performance Optimizer                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  IMMUTABLE RULES:                                                            ║
║  ✓ Bot is ALWAYS and ONLY a trading bot                                      ║
║  ✓ Reward system CANNOT be changed                                           ║
║  ✓ Bot's fundamental purpose CANNOT be changed                               ║
║  ✓ All improvements strengthen: intelligence, stability, safety, profit      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DeepSeek AI Engineer - 24/7 Autonomous System'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='full_autonomous',
        choices=['full_autonomous', 'supervised', 'maintenance_only', 'evolution_only', 'research_only'],
        help='Operating mode'
    )
    
    parser.add_argument(
        '--single-cycle',
        action='store_true',
        help='Run a single cycle instead of continuous operation'
    )
    
    parser.add_argument(
        '--maintenance-interval',
        type=int,
        default=24,
        help='Hours between maintenance cycles (default: 24)'
    )
    
    parser.add_argument(
        '--evolution-interval',
        type=int,
        default=6,
        help='Hours between evolution cycles (default: 6)'
    )
    
    parser.add_argument(
        '--security-interval',
        type=int,
        default=12,
        help='Hours between security scans (default: 12)'
    )
    
    return parser.parse_args()


async def run_continuous(orchestrator: DeepSeekOrchestrator):
    """Run the orchestrator continuously."""
    logger.info("Starting continuous 24/7 operation...")
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        await orchestrator.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await orchestrator.stop()
        raise


async def run_single_cycle(orchestrator: DeepSeekOrchestrator):
    """Run a single cycle."""
    logger.info("Running single cycle...")
    
    results = await orchestrator.run_single_cycle()
    
    print("\n" + "=" * 60)
    print("SINGLE CYCLE RESULTS")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Purpose Integrity: {'✓ VALID' if results['purpose_integrity'] else '✗ COMPROMISED'}")
    print()
    
    if results['maintenance']:
        print("MAINTENANCE:")
        for key, value in results['maintenance'].items():
            print(f"  {key}: {value}")
    
    if results['evolution']:
        print("\nEVOLUTION:")
        for key, value in results['evolution'].items():
            print(f"  {key}: {value}")
    
    if results['security']:
        print("\nSECURITY:")
        for key, value in results['security'].items():
            print(f"  {key}: {value}")
    
    if results['performance']:
        print("\nPERFORMANCE:")
        for key, value in results['performance'].items():
            print(f"  {key}: {value}")
    
    print("=" * 60)
    
    return results


async def main():
    """Main entry point."""
    print_banner()
    args = parse_args()
    
    # Verify purpose integrity before starting
    logger.info("Verifying purpose integrity...")
    purpose_valid, msg = verify_purpose_integrity()
    
    if not purpose_valid:
        logger.critical(f"PURPOSE INTEGRITY FAILED: {msg}")
        logger.critical("Cannot start DeepSeek AI Engineer with compromised purpose")
        sys.exit(1)
    
    logger.info("Purpose integrity verified ✓")
    
    # Create configuration
    mode_map = {
        'full_autonomous': OrchestratorMode.FULL_AUTONOMOUS,
        'supervised': OrchestratorMode.SUPERVISED,
        'maintenance_only': OrchestratorMode.MAINTENANCE_ONLY,
        'evolution_only': OrchestratorMode.EVOLUTION_ONLY,
        'research_only': OrchestratorMode.RESEARCH_ONLY,
    }
    
    config = OrchestratorConfig(
        mode=mode_map[args.mode],
        maintenance_interval_hours=args.maintenance_interval,
        evolution_interval_hours=args.evolution_interval,
        security_scan_interval_hours=args.security_interval,
    )
    
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Maintenance interval: {config.maintenance_interval_hours}h")
    logger.info(f"Evolution interval: {config.evolution_interval_hours}h")
    logger.info(f"Security scan interval: {config.security_scan_interval_hours}h")
    
    # Create orchestrator
    try:
        orchestrator = DeepSeekOrchestrator(project_root, config)
    except Exception as e:
        logger.critical(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)
    
    # Run
    if args.single_cycle:
        await run_single_cycle(orchestrator)
    else:
        await run_continuous(orchestrator)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
