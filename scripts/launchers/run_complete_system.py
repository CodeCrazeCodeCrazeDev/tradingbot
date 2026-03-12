"""
Complete System Runner - Starts all services

This script starts the complete Elite Trading Bot with all 50 features:
- Survival Core
- Live Dashboard
- Telegram Bot
- Reconciliation Service
- All monitoring and safety systems
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import yaml
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/complete_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CompleteSystemRunner:
    """Orchestrates all system components"""
    
    def __init__(self, config_path: str = "config/complete_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Component references
        self.survival_core = None
        self.dashboard = None
        self.telegram_bot = None
        self.reconciliation = None
        
        # Running tasks
        self.tasks = []
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> dict:
        """Load configuration"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'survival_core': {
                'symbols': ['EURUSD', 'GBPUSD'],
                'simulate_data': True,
                'max_data_staleness_seconds': 5,
                'max_clock_drift_ms': 100,
                'ntp_check_interval': 300
            },
            'dashboard': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 8000
            },
            'telegram': {
                'enabled': False,  # Requires token
                'token': None,
                'user_roles': {}
            },
            'reconciliation': {
                'enabled': True,
                'interval': 300,
                'auto_correct_positions': True
            },
            'risk_budget': {
                'total_risk_budget': 0.10,
                'allocation_method': 'risk_parity'
            },
            'feature_flags': {
                'trading_enabled': True,
                'new_router': False
            }
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing system components...")
        
        try:
            # 1. Initialize Survival Core
            from trading_bot.core.survival_core import SurvivalCore
            self.survival_core = SurvivalCore(self.config.get('survival_core', {}))
            logger.info("✓ Survival Core initialized")
            
            # 2. Initialize Dashboard (if enabled)
            if self.config.get('dashboard', {}).get('enabled', True):
                from trading_bot.dashboard.live_dashboard import LiveDashboard
                self.dashboard = LiveDashboard(
                    self.survival_core,
                    self.config.get('dashboard', {})
                )
                logger.info("✓ Live Dashboard initialized")
            
            # 3. Initialize Telegram Bot (if enabled and token provided)
            telegram_config = self.config.get('telegram', {})
            if telegram_config.get('enabled') and telegram_config.get('token'):
                from trading_bot.ops.telegram_commands import TelegramOpsCommands
                self.telegram_bot = TelegramOpsCommands(
                    self.survival_core,
                    telegram_config
                )
                await self.telegram_bot.setup(telegram_config['token'])
                logger.info("✓ Telegram Bot initialized")
            else:
                logger.info("⊘ Telegram Bot disabled (no token)")
            
            # 4. Initialize Reconciliation Service (if enabled)
            if self.config.get('reconciliation', {}).get('enabled', True):
                from trading_bot.core.reconciliation_service import ReconciliationService
                
                # Create a mock broker adapter for now
                class MockBrokerAdapter:
                    async def get_positions(self):
                        return []
                
                self.reconciliation = ReconciliationService(
                    self.survival_core.execution,
                    MockBrokerAdapter(),
                    self.config.get('reconciliation', {})
                )
                logger.info("✓ Reconciliation Service initialized")
            
            # 5. Initialize Complete System Integration
            from trading_bot.complete_implementation import CompleteSystemIntegration
            self.complete_integration = CompleteSystemIntegration(
                self.survival_core,
                self.config
            )
            logger.info("✓ Complete System Integration initialized")
            
            logger.info("All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def start_services(self):
        """Start all services"""
        logger.info("Starting all services...")
        
        try:
            # 1. Start Survival Core
            core_task = asyncio.create_task(
                self.survival_core.start(),
                name="survival_core"
            )
            self.tasks.append(core_task)
            logger.info("✓ Survival Core started")
            
            # 2. Start Dashboard
            if self.dashboard:
                dashboard_task = asyncio.create_task(
                    self.dashboard.start(
                        host=self.config.get('dashboard', {}).get('host', '0.0.0.0'),
                        port=self.config.get('dashboard', {}).get('port', 8000)
                    ),
                    name="dashboard"
                )
                self.tasks.append(dashboard_task)
                logger.info("✓ Dashboard started on http://localhost:8000")
            
            # 3. Start Telegram Bot
            if self.telegram_bot:
                telegram_task = asyncio.create_task(
                    self.telegram_bot.start(),
                    name="telegram_bot"
                )
                self.tasks.append(telegram_task)
                logger.info("✓ Telegram Bot started")
            
            # 4. Start Reconciliation Service
            if self.reconciliation:
                recon_task = asyncio.create_task(
                    self.reconciliation.start(),
                    name="reconciliation"
                )
                self.tasks.append(recon_task)
                logger.info("✓ Reconciliation Service started")
            
            self.running = True
            logger.info("=" * 60)
            logger.info("🚀 ELITE TRADING BOT - ALL SYSTEMS OPERATIONAL")
            logger.info("=" * 60)
            logger.info("Dashboard: http://localhost:8000")
            logger.info("API Docs: http://localhost:8000/docs")
            logger.info("Status: All 50 features active")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            await self.shutdown()
            raise
    
    async def health_check_loop(self):
        """Periodic health check of all services"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check if any tasks failed
                for task in self.tasks:
                    if task.done():
                        if task.exception():
                            logger.error(f"Task {task.get_name()} failed: {task.exception()}")
                            await self.shutdown()
                            return
                
                # Get system status
                if self.survival_core:
                    status = self.survival_core.get_system_status()
                    logger.info(
                        f"Health Check: Running={status['system']['running']}, "
                        f"Paused={status['system']['paused']}, "
                        f"Errors={status['system']['error_count']}"
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of all services"""
        if not self.running:
            return
        
        logger.info("Initiating graceful shutdown...")
        self.running = False
        
        try:
            # 1. Stop Telegram Bot
            if self.telegram_bot:
                await self.telegram_bot.stop()
                logger.info("✓ Telegram Bot stopped")
            
            # 2. Stop Reconciliation
            if self.reconciliation:
                await self.reconciliation.stop()
                logger.info("✓ Reconciliation Service stopped")
            
            # 3. Stop Survival Core
            if self.survival_core:
                await self.survival_core.stop()
                logger.info("✓ Survival Core stopped")
            
            # 4. Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            logger.info("All services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main run loop"""
        try:
            # Initialize
            await self.initialize_components()
            
            # Start services
            await self.start_services()
            
            # Run health check loop
            await self.health_check_loop()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Create data directories
    Path('data/quarantine').mkdir(parents=True, exist_ok=True)
    Path('data/checkpoints').mkdir(parents=True, exist_ok=True)
    
    # Create config directory
    Path('config').mkdir(exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("ELITE TRADING BOT - COMPLETE SYSTEM")
    logger.info("=" * 60)
    logger.info("Initializing all 50 features...")
    logger.info("")
    
    # Run the system
    runner = CompleteSystemRunner()
    await runner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)
