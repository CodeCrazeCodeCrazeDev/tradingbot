"""
Production Runner - Complete system orchestration for production deployment
Manages all trading bot components with health monitoring and auto-recovery
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a service."""
    name: str
    module: str
    enabled: bool = True
    auto_restart: bool = True
    max_restarts: int = 3
    restart_delay: int = 5


class ProductionRunner:
    """
    Production-grade system runner with:
    - Multi-service orchestration
    - Health monitoring
    - Auto-recovery
    - Graceful shutdown
    - Performance tracking
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize production runner."""
        logger.info("="*80)
        logger.info("🚀 PRODUCTION RUNNER INITIALIZING")
        logger.info("="*80)
        
        self.config = self._load_config(config_file)
        self.services: Dict[str, Any] = {}
        self.service_tasks: Dict[str, asyncio.Task] = {}
        self.restart_counts: Dict[str, int] = {}
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.connection_monitor = None
        
        # CRITICAL SAFETY: Enforce paper trading mode
        if 'trading_mode' not in self.config:
            self.config['trading_mode'] = 'paper'
            logger.warning("⚠️ SAFETY: Trading mode not specified, defaulting to PAPER mode")
        
        if self.config.get('trading_mode') == 'live':
            logger.critical("🚨 LIVE TRADING BLOCKED - MANUAL APPROVAL REQUIRED 🚨")
            logger.critical("🚨 Edit production_runner.py to enable live trading 🚨")
            self.config['trading_mode'] = 'paper'  # Force paper mode
        
        # Service definitions
        self.service_configs = [
            ServiceConfig('health_monitor', 'system_health_monitor', enabled=True),
            ServiceConfig('integrated_system', 'integrated_trading_system', enabled=True),
            ServiceConfig('alphaalgo', 'alphaalgo_2_0', enabled=False),  # Alternative
        ]
        
        logger.info(f"✅ Production Runner initialized with {len(self.service_configs)} services")
        logger.info(f"📋 Trading Mode: {self.config['trading_mode'].upper()}")
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config file: {e}, using defaults")
        
        return {
            'environment': 'production',
            'log_level': 'INFO',
            'enable_monitoring': True,
            'enable_auto_recovery': True,
            'max_restart_attempts': 3,
            'health_check_interval': 60,
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'risk_per_trade': 0.01,
            'max_positions': 3
        }
    
    async def start(self):
        """Start all services."""
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING PRODUCTION SYSTEM")
        logger.info("="*80)
        
        self.is_running = True
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Initialize connection monitor
        await self._init_connection_monitor()
        
        # Start enabled services
        for service_config in self.service_configs:
            if service_config.enabled:
                await self._start_service(service_config)
        
        logger.info("\n✅ All services started")
        logger.info("="*80)
        
        # Monitor services
        await self._monitor_services()
    
    async def _init_connection_monitor(self):
        """Initialize and start connection monitoring."""
        try:
            from trading_bot.connectivity.connection_monitor import ConnectionMonitor
            
            self.connection_monitor = ConnectionMonitor(
                check_interval=30,
                max_consecutive_failures=3
            )
            
            # Start monitoring in background
            asyncio.create_task(self.connection_monitor.start())
            
            logger.info("✅ Connection Monitor started")
        except Exception as e:
            logger.warning(f"⚠️ Connection Monitor failed to start: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"\n🛑 Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logger.warning(f"⚠️ Could not setup signal handlers: {e}")
    
    async def _start_service(self, service_config: ServiceConfig):
        """Start a single service."""
        try:
            logger.info(f"🔄 Starting service: {service_config.name}")
            
            # Import and initialize service
            service = await self._initialize_service(service_config)
            
            if service:
                self.services[service_config.name] = service
                
                # Start service task
                task = asyncio.create_task(
                    self._run_service(service_config, service),
                    name=service_config.name
                )
                self.service_tasks[service_config.name] = task
                
                logger.info(f"✅ Service started: {service_config.name}")
            else:
                logger.error(f"❌ Failed to initialize service: {service_config.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to start service {service_config.name}: {e}")
    
    async def _initialize_service(self, service_config: ServiceConfig) -> Optional[Any]:
        """Initialize a service instance."""
        try:
            if service_config.module == 'system_health_monitor':
                from system_health_monitor import SystemHealthMonitor
                return SystemHealthMonitor(check_interval=self.config['health_check_interval'])
            
            elif service_config.module == 'integrated_trading_system':
                from integrated_trading_system import IntegratedTradingSystem
                return IntegratedTradingSystem(config=self.config)
            
            elif service_config.module == 'alphaalgo_2_0':
                from alphaalgo_2_0 import AlphaAlgo2_0
                return AlphaAlgo2_0()
            
            else:
                logger.warning(f"⚠️ Unknown service module: {service_config.module}")
                return None
                
        except ImportError as e:
            logger.error(f"❌ Failed to import {service_config.module}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to initialize {service_config.name}: {e}")
            return None
    
    async def _run_service(self, service_config: ServiceConfig, service: Any):
        """Run a service with auto-recovery."""
        restart_count = 0
        
        while self.is_running and restart_count < service_config.max_restarts:
            try:
                logger.info(f"▶️ Running service: {service_config.name}")
                
                # Run the service
                if hasattr(service, 'run'):
                    await service.run()
                elif hasattr(service, 'start'):
                    await service.start()
                else:
                    logger.error(f"❌ Service {service_config.name} has no run/start method")
                    break
                
                # If we get here, service stopped normally
                logger.info(f"⏹️ Service stopped: {service_config.name}")
                break
                
            except Exception as e:
                logger.error(f"❌ Service {service_config.name} crashed: {e}")
                
                if service_config.auto_restart and restart_count < service_config.max_restarts:
                    restart_count += 1
                    logger.info(f"🔄 Restarting {service_config.name} (attempt {restart_count}/{service_config.max_restarts})")
                    await asyncio.sleep(service_config.restart_delay)
                    
                    # Reinitialize service
                    service = await self._initialize_service(service_config)
                    if not service:
                        logger.error(f"❌ Failed to reinitialize {service_config.name}")
                        break
                else:
                    logger.error(f"❌ Service {service_config.name} exceeded max restarts")
                    break
        
        self.restart_counts[service_config.name] = restart_count
    
    async def _monitor_services(self):
        """Monitor running services."""
        logger.info("👁️ Service monitoring started")
        
        try:
            while self.is_running:
                # Check service tasks
                for name, task in list(self.service_tasks.items()):
                    if task.done():
                        logger.warning(f"⚠️ Service task completed: {name}")
                        
                        # Check if it crashed
                        try:
                            task.result()
                        except Exception as e:
                            logger.error(f"❌ Service {name} failed: {e}")
                
                # Wait before next check
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            logger.info("👁️ Service monitoring stopped")
    
    async def shutdown(self):
        """Graceful shutdown of all services."""
        logger.info("\n" + "="*80)
        logger.info("🛑 INITIATING GRACEFUL SHUTDOWN")
        logger.info("="*80)
        
        self.is_running = False
        
        # Stop all services
        for name, service in self.services.items():
            try:
                logger.info(f"🔄 Stopping service: {name}")
                
                if hasattr(service, 'stop'):
                    service.stop()
                elif hasattr(service, 'shutdown'):
                    await service.shutdown()
                
                logger.info(f"✅ Service stopped: {name}")
                
            except Exception as e:
                logger.error(f"❌ Error stopping service {name}: {e}")
        
        # Cancel all tasks
        for name, task in self.service_tasks.items():
            if not task.done():
                logger.info(f"🔄 Cancelling task: {name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Generate final report
        self._generate_shutdown_report()
        
        logger.info("\n" + "="*80)
        logger.info("✅ SHUTDOWN COMPLETE")
        logger.info("="*80)
        
        self.shutdown_event.set()
    
    def _generate_shutdown_report(self):
        """Generate shutdown report."""
        report = {
            'shutdown_time': datetime.now().isoformat(),
            'services_run': list(self.services.keys()),
            'restart_counts': self.restart_counts,
            'config': self.config
        }
        
        try:
            with open('logs/shutdown_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            logger.info("📄 Shutdown report saved")
        except Exception as e:
            logger.error(f"❌ Failed to save shutdown report: {e}")
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()


async def main():
    """Main entry point."""
    import os
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('knowledge', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Initialize and run production system
    runner = ProductionRunner()
    
    try:
        # Start all services
        await runner.start()
        
        # Wait for shutdown signal
        await runner.wait_for_shutdown()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Keyboard interrupt received")
        await runner.shutdown()
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await runner.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
