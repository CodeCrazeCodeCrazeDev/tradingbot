"""
Autonomous Learning Session Runner

Runs a 2-hour autonomous learning session where the bot:
1. Accesses the internet to learn trading
2. Reads books, research papers, articles
3. Learns from basic to advanced levels
4. Tests itself with evolving difficulty (easy to super-hard)
5. Transfers learned knowledge to the trading bot
6. Monitors progress and evolves

Usage:
    python run_autonomous_learning.py
    python run_autonomous_learning.py --hours 2
    python run_autonomous_learning.py --mode intensive
"""

import asyncio
import argparse
import logging
import sys
import signal
import os
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.autonomous_learner import (
    LearningOrchestrator,
    LearningSessionConfig,
    LearningMode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'autonomous_learning_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
    ]
)

logger = logging.getLogger(__name__)

# Global orchestrator for signal handling
orchestrator = None


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("\n⚠️ Interrupt received. Stopping learning session gracefully...")
    if orchestrator:
        orchestrator.stop()


async def run_learning_session(hours: float, mode: str, start_level: int, target_level: int):
    """Run the autonomous learning session"""
    global orchestrator
    
    # Parse mode
    mode_map = {
        'intensive': LearningMode.INTENSIVE,
        'balanced': LearningMode.BALANCED,
        'thorough': LearningMode.THOROUGH,
    }
    learning_mode = mode_map.get(mode.lower(), LearningMode.BALANCED)
    
    # Create configuration
    config = LearningSessionConfig(
        duration_hours=hours,
        mode=learning_mode,
        start_level=start_level,
        target_level=target_level,
        min_accuracy_to_advance=0.7,
        tests_per_level=3,
        resources_per_topic=3,
        auto_transfer=True,
    )
    
    print("\n" + "="*70)
    print("[BOT] AUTONOMOUS LEARNING SESSION")
    print("="*70)
    print(f"[TIME] Duration: {hours} hours")
    print(f"[MODE] Mode: {learning_mode.name}")
    print(f"[LEVEL] Levels: {start_level} -> {target_level}")
    print(f"[TARGET] Min accuracy to advance: 70%")
    print(f"[TEST] Tests per level: 3")
    print(f"[TRANSFER] Auto-transfer: Enabled")
    print("="*70)
    print("\n[START] Starting learning session...\n")
    print("Press Ctrl+C to stop gracefully\n")
    
    # Create orchestrator
    orchestrator = LearningOrchestrator()
    # Run session
    try:
        result = await orchestrator.run_learning_session(config)
        
        # Print final results
        print("\n" + "="*70)
        print("[COMPLETE] LEARNING SESSION COMPLETE")
        print("="*70)
        print(f"[ID] Session ID: {result.session_id}")
        print(f"[TIME] Duration: {result.end_time - result.start_time}")
        print(f"[LEVEL] Final Level: {result.final_level}/7")
        print(f"[RESOURCES] Resources Studied: {result.resources_studied}")
        print(f"[CONCEPTS] Concepts Learned: {result.concepts_learned}")
        print(f"[TESTS] Tests Taken: {result.tests_taken}")
        print(f"[PASSED] Tests Passed: {result.tests_passed}")
        print(f"[ACCURACY] Final Accuracy: {result.final_accuracy:.1%}")
        print(f"[TRANSFER] Knowledge Transferred: {result.knowledge_transferred}")
        print(f"[EVOLUTION] Evolution Cycles: {result.evolution_cycles}")
        print(f"{'[SUCCESS] SUCCESS!' if result.success else '[CONTINUE] More learning needed'}")
        print("="*70)
        
        return result
        
    except KeyboardInterrupt:
        logger.info("Session interrupted by user")
        return None
    except Exception as e:
        logger.error(f"Session error: {e}")
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run autonomous trading learning session',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_autonomous_learning.py                    # Default 2-hour session
    python run_autonomous_learning.py --hours 1          # 1-hour session
    python run_autonomous_learning.py --mode intensive   # Fast-paced learning
    python run_autonomous_learning.py --mode thorough    # Deep understanding
    python run_autonomous_learning.py --target 5         # Stop at level 5
        """
    )
    
    parser.add_argument(
        '--hours', '-t',
        type=float,
        default=2.0,
        help='Duration of learning session in hours (default: 2.0)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        type=str,
        choices=['intensive', 'balanced', 'thorough'],
        default='balanced',
        help='Learning mode (default: balanced)'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=int,
        default=1,
        choices=range(1, 8),
        help='Starting difficulty level 1-7 (default: 1)'
    )
    
    parser.add_argument(
        '--target', '-g',
        type=int,
        default=7,
        choices=range(1, 8),
        help='Target difficulty level 1-7 (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the session
    try:
        result = asyncio.run(run_learning_session(
            hours=args.hours,
            mode=args.mode,
            start_level=args.start,
            target_level=args.target,
        ))
        
        if result and result.success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
