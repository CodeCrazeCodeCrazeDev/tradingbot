"""
Master Runner - Unified Entry Point for AlphaAlgo Trading Bot
Integrates all 4 layers:
- Layer 1: Core Trading Systems (main.py)
- Layer 2: Background Services (background_services.py)
- Layer 3: Scheduled Jobs (scheduled_jobs_runner.py)
- Layer 4: Intelligent Delegation (on-demand)

This is the MASTER orchestrator that runs everything together.
"""

import asyncio
import logging
import os
import sys
import signal
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# CRITICAL: Apply UTF-8 encoding fix FIRST
# ============================================================================
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# Configure logging with UTF-8 encoding
Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/master_runner.log', encoding='utf-8', errors='replace'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MasterRunner')


class SystemLayer(Enum):
    """System layers."""
    LAYER1_TRADING = "trading"
    LAYER2_BACKGROUND = "background"
    LAYER3_SCHEDULED = "scheduled"
    LAYER4_DELEGATION = "delegation"


@dataclass
class LayerStatus:
    """Status of a system layer."""
    layer: SystemLayer
    running: bool = False
    started_at: Optional[datetime] = None
    error: Optional[str] = None
    task: Optional[asyncio.Task] = None


class MasterRunner:
    """
    Master Runner - Orchestrates all 4 layers of the trading system.
    
    Layer 1: Core Trading (main.py)
        - Elite AI System
        - Market Intelligence
        - Risk Management
        - Smart Execution
        
    Layer 2: Background Services
        - Market Student (learning)
        - Eternal Evolution (auto-tuning)
        - Self-Diagnostic (health)
        - Risk Monitor (real-time)
        
    Layer 3: Scheduled Jobs
        - Offline RL Training (nightly)
        - Neural Evolution (nightly)
        - Adversarial Testing (weekly)
        - Performance Analysis (daily)
        
    Layer 4: Intelligent Delegation (on-demand)
        - Multi-agent coordination
        - Task decomposition
        - Trust/reputation management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.layers: Dict[SystemLayer, LayerStatus] = {
            layer: LayerStatus(layer=layer) for layer in SystemLayer
        }
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Component instances
        self.background_manager = None
        self.scheduler_thread = None
        self.trading_task = None
        
    async def start_layer1_trading(self, args: Optional[List[str]] = None):
        """Start Layer 1: Core Trading Systems."""
        logger.info("=" * 70)
        logger.info("STARTING LAYER 1: CORE TRADING SYSTEMS")
        logger.info("=" * 70)
        
        try:
            # Import main module
            import main
            
            # Run main trading loop
            self.layers[SystemLayer.LAYER1_TRADING].running = True
            self.layers[SystemLayer.LAYER1_TRADING].started_at = datetime.now()
            
            await main.main(args)
            
        except ImportError as e:
            logger.error(f"Failed to import main.py: {e}")
            self.layers[SystemLayer.LAYER1_TRADING].error = str(e)
        except Exception as e:
            logger.error(f"Layer 1 error: {e}")
            self.layers[SystemLayer.LAYER1_TRADING].error = str(e)
        finally:
            self.layers[SystemLayer.LAYER1_TRADING].running = False
    
    async def start_layer2_background(self):
        """Start Layer 2: Background Services."""
        logger.info("=" * 70)
        logger.info("STARTING LAYER 2: BACKGROUND SERVICES")
        logger.info("=" * 70)
        
        try:
            from background_services import BackgroundServicesManager
            
            self.background_manager = BackgroundServicesManager(self.config)
            
            self.layers[SystemLayer.LAYER2_BACKGROUND].running = True
            self.layers[SystemLayer.LAYER2_BACKGROUND].started_at = datetime.now()
            
            # Start all background services
            await self.background_manager.start_all()
            
            logger.info("[OK] Layer 2 Background Services started")
            
        except ImportError as e:
            logger.error(f"Failed to import background_services: {e}")
            self.layers[SystemLayer.LAYER2_BACKGROUND].error = str(e)
        except Exception as e:
            logger.error(f"Layer 2 error: {e}")
            self.layers[SystemLayer.LAYER2_BACKGROUND].error = str(e)
    
    def start_layer3_scheduled(self):
        """Start Layer 3: Scheduled Jobs (in separate thread)."""
        logger.info("=" * 70)
        logger.info("STARTING LAYER 3: SCHEDULED JOBS")
        logger.info("=" * 70)
        
        try:
            from scheduled_jobs_runner import schedule_jobs, run_scheduler
            import schedule
            import time
            
            def scheduler_loop():
                """Run scheduler in background thread."""
                schedule_jobs()
                while self.running:
                    schedule.run_pending()
                    time.sleep(60)
            
            self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            self.layers[SystemLayer.LAYER3_SCHEDULED].running = True
            self.layers[SystemLayer.LAYER3_SCHEDULED].started_at = datetime.now()
            
            logger.info("[OK] Layer 3 Scheduled Jobs started")
            
        except ImportError as e:
            logger.error(f"Failed to import scheduled_jobs_runner: {e}")
            self.layers[SystemLayer.LAYER3_SCHEDULED].error = str(e)
        except Exception as e:
            logger.error(f"Layer 3 error: {e}")
            self.layers[SystemLayer.LAYER3_SCHEDULED].error = str(e)
    
    async def start_layer4_delegation(self):
        """Start Layer 4: Intelligent Delegation (on-demand)."""
        logger.info("=" * 70)
        logger.info("STARTING LAYER 4: INTELLIGENT DELEGATION")
        logger.info("=" * 70)
        
        try:
            from trading_bot.intelligent_delegation import quick_start
            
            self.delegation_orchestrator = quick_start()
            
            self.layers[SystemLayer.LAYER4_DELEGATION].running = True
            self.layers[SystemLayer.LAYER4_DELEGATION].started_at = datetime.now()
            
            logger.info("[OK] Layer 4 Intelligent Delegation ready")
            
        except ImportError as e:
            logger.warning(f"Intelligent Delegation not available: {e}")
            self.layers[SystemLayer.LAYER4_DELEGATION].error = str(e)
        except Exception as e:
            logger.error(f"Layer 4 error: {e}")
            self.layers[SystemLayer.LAYER4_DELEGATION].error = str(e)
    
    async def start_all_layers(self, trading_args: Optional[List[str]] = None):
        """Start all 4 layers."""
        self.running = True
        
        logger.info("=" * 70)
        logger.info("ALPHAALGO MASTER RUNNER - STARTING ALL LAYERS")
        logger.info("=" * 70)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 70)
        
        # Start Layer 2 first (background services)
        await self.start_layer2_background()
        
        # Start Layer 3 (scheduled jobs)
        self.start_layer3_scheduled()
        
        # Start Layer 4 (intelligent delegation)
        await self.start_layer4_delegation()
        
        # Start Layer 1 last (main trading loop)
        # This runs in the foreground
        await self.start_layer1_trading(trading_args)
    
    async def stop_all_layers(self):
        """Stop all layers gracefully."""
        logger.info("Stopping all layers...")
        self.running = False
        
        # Stop Layer 2
        if self.background_manager:
            await self.background_manager.stop_all()
            self.layers[SystemLayer.LAYER2_BACKGROUND].running = False
        
        # Stop Layer 3 (thread will exit when self.running = False)
        self.layers[SystemLayer.LAYER3_SCHEDULED].running = False
        
        # Stop Layer 4
        self.layers[SystemLayer.LAYER4_DELEGATION].running = False
        
        # Stop Layer 1
        self.layers[SystemLayer.LAYER1_TRADING].running = False
        
        logger.info("All layers stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all layers."""
        return {
            layer.value: {
                'running': status.running,
                'started_at': status.started_at.isoformat() if status.started_at else None,
                'error': status.error,
            }
            for layer, status in self.layers.items()
        }
    
    def print_status(self):
        """Print status of all layers."""
        print("\n" + "=" * 70)
        print("ALPHAALGO SYSTEM STATUS")
        print("=" * 70)
        
        for layer, status in self.layers.items():
            icon = "[OK]" if status.running else "[X]"
            state = "RUNNING" if status.running else "STOPPED"
            if status.error:
                state = f"ERROR: {status.error[:30]}..."
            print(f"  {icon} Layer {layer.value:12} - {state}")
        
        print("=" * 70 + "\n")


# ============================================================================
# QUICK START FUNCTIONS
# ============================================================================

async def quick_start_full(trading_args: Optional[List[str]] = None) -> MasterRunner:
    """Quick start with all layers."""
    runner = MasterRunner()
    await runner.start_all_layers(trading_args)
    return runner


async def quick_start_trading_only(trading_args: Optional[List[str]] = None) -> MasterRunner:
    """Quick start with trading only (Layer 1)."""
    runner = MasterRunner()
    await runner.start_layer1_trading(trading_args)
    return runner


async def quick_start_background_only() -> MasterRunner:
    """Quick start with background services only (Layer 2)."""
    runner = MasterRunner()
    runner.running = True
    await runner.start_layer2_background()
    return runner


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Master Runner - Unified Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python master_runner.py --full                    # Start all 4 layers
  python master_runner.py --trading-only            # Start trading only
  python master_runner.py --background-only         # Start background services only
  python master_runner.py --scheduled-only          # Start scheduled jobs only
  python master_runner.py --status                  # Show system status
  
Trading Arguments (passed to main.py):
  python master_runner.py --full -- --symbol EURUSD --mode paper
        """
    )
    
    parser.add_argument('--full', action='store_true', 
                       help='Start all 4 layers (recommended)')
    parser.add_argument('--trading-only', action='store_true',
                       help='Start Layer 1 (trading) only')
    parser.add_argument('--background-only', action='store_true',
                       help='Start Layer 2 (background services) only')
    parser.add_argument('--scheduled-only', action='store_true',
                       help='Start Layer 3 (scheduled jobs) only')
    parser.add_argument('--status', action='store_true',
                       help='Show system status')
    parser.add_argument('trading_args', nargs='*',
                       help='Arguments to pass to main.py')
    
    args = parser.parse_args()
    
    runner = MasterRunner()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(runner.stop_all_layers())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.status:
            runner.print_status()
            return
        
        if args.trading_only:
            await runner.start_layer1_trading(args.trading_args)
        elif args.background_only:
            runner.running = True
            await runner.start_layer2_background()
            # Keep running
            while runner.running:
                await asyncio.sleep(60)
                runner.print_status()
        elif args.scheduled_only:
            runner.running = True
            runner.start_layer3_scheduled()
            # Keep running
            while runner.running:
                await asyncio.sleep(60)
        elif args.full or not any([args.trading_only, args.background_only, args.scheduled_only]):
            await runner.start_all_layers(args.trading_args)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await runner.stop_all_layers()
        logger.info("Master Runner shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
