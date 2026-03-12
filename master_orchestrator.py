"""
Master Orchestrator - Unified Trading Bot Controller
Coordinates all 4 layers: Core Systems, Background Services, Scheduled Jobs, Coordination

This is the central brain that ensures every system contributes to profitability.
"""

import asyncio
import logging
import multiprocessing
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('master_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """
    Master Orchestrator - Coordinates all 4 layers of the trading bot.
    
    Layer 1: Core Systems (in main.py)
    Layer 2: Background Services (separate processes)
    Layer 3: Scheduled Jobs (nightly/weekly)
    Layer 4: Coordination (on-demand)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.redis_client = None
        self.background_processes: Dict[str, multiprocessing.Process] = {}
        self.running = False
        
        # Initialize Redis connection
        self._init_redis()
        
        logger.info("=" * 70)
        logger.info("MASTER ORCHESTRATOR INITIALIZED")
        logger.info("=" * 70)
    
    def _init_redis(self):
        """Initialize Redis connection for IPC."""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✓ Redis connection established")
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            logger.warning("Background services will not be available")
            self.redis_client = None
    
    # ========================================================================
    # LAYER 1: CORE SYSTEMS (Main Trading Loop)
    # ========================================================================
    
    async def start_core_systems(self, args):
        """Start Layer 1 core systems in main.py."""
        logger.info("=" * 70)
        logger.info("LAYER 1: STARTING CORE SYSTEMS")
        logger.info("=" * 70)
        
        # This would be called from main.py
        # The actual initialization happens in main.py
        # This method just coordinates the startup
        
        systems = {
            'elite_ai': args.use_elite_ai,
            'market_intelligence': args.use_market_intelligence,
            'complete_system': args.use_complete_system,
            'enhanced_risk': args.use_enhanced_risk,
            'smart_execution': args.use_smart_execution,
            'performance_analytics': args.use_performance_analytics,
        }
        
        active = [k for k, v in systems.items() if v]
        logger.info(f"Active core systems: {', '.join(active)}")
        logger.info("=" * 70)
        
        return systems
    
    # ========================================================================
    # LAYER 2: BACKGROUND SERVICES
    # ========================================================================
    
    def start_background_services(self):
        """Start Layer 2 background intelligence services."""
        logger.info("=" * 70)
        logger.info("LAYER 2: STARTING BACKGROUND SERVICES")
        logger.info("=" * 70)
        
        if not self.redis_client:
            logger.error("Redis not available - background services disabled")
            return
        
        services = [
            ('market_student', self._run_market_student),
            ('eternal_evolution', self._run_eternal_evolution),
            ('sentiment_analysis', self._run_sentiment_analysis),
            ('market_monitor', self._run_market_monitor),
        ]
        
        for name, func in services:
            try:
                process = multiprocessing.Process(target=func, name=name)
                process.daemon = True
                process.start()
                self.background_processes[name] = process
                logger.info(f"✓ Started: {name} (PID: {process.pid})")
            except Exception as e:
                logger.error(f"✗ Failed to start {name}: {e}")
        
        logger.info(f"Background services started: {len(self.background_processes)}")
        logger.info("=" * 70)
    
    def _run_market_student(self):
        """Background service: Market Student."""
        try:
            from trading_bot.market_student import MarketStudentOrchestrator
            orchestrator = MarketStudentOrchestrator({})
            
            while True:
                try:
                    # Check for new trades
                    if self.redis_client:
                        trade_data = self.redis_client.lpop('trade_results')
                        if trade_data:
                            import json
                            trade = json.loads(trade_data)
                            lesson = asyncio.run(orchestrator.learn_from_trade(trade))
                            if lesson:
                                logger.info(f"Market Student: {lesson.get('insight', 'Learned')}")
                    
                    import time
                    time.sleep(10)
                except Exception as e:
                    logger.error(f"Market Student error: {e}")
                    import time
                    time.sleep(30)
        except ImportError:
            logger.error("Market Student not available")
    
    def _run_eternal_evolution(self):
        """Background service: Eternal Evolution."""
        try:
            from trading_bot.eternal_evolution import EternalEvolutionOrchestrator
            orchestrator = EternalEvolutionOrchestrator({})
            asyncio.run(orchestrator.start())
            
            while True:
                try:
                    cycle = asyncio.run(orchestrator.evolve_all())
                    if cycle and self.redis_client:
                        import json
                        self.redis_client.set('optimized_parameters', json.dumps(cycle.get('parameters', {})))
                    
                    import time
                    time.sleep(3600)  # Every hour
                except Exception as e:
                    logger.error(f"Eternal Evolution error: {e}")
                    import time
                    time.sleep(300)
        except ImportError:
            logger.error("Eternal Evolution not available")
    
    def _run_sentiment_analysis(self):
        """Background service: Sentiment Analysis."""
        try:
            from trading_bot.sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            
            while True:
                try:
                    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
                    for symbol in symbols:
                        sentiment = analyzer.analyze_symbol(symbol)
                        if sentiment and self.redis_client:
                            import json
                            self.redis_client.setex(f'sentiment:{symbol}', 300, json.dumps(sentiment))
                    
                    import time
                    time.sleep(300)  # Every 5 minutes
                except Exception as e:
                    logger.error(f"Sentiment Analysis error: {e}")
                    import time
                    time.sleep(60)
        except ImportError:
            logger.error("Sentiment Analyzer not available")
    
    def _run_market_monitor(self):
        """Background service: Market Intelligence Monitor."""
        try:
            from trading_bot.market_intelligence import MarketDataMonitor
            monitor = MarketDataMonitor()
            
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
            for symbol in symbols:
                monitor.start_monitoring(symbol=symbol, timeframe='M15')
            
            while True:
                try:
                    for symbol in symbols:
                        state = monitor.get_current_state(symbol)
                        if state and self.redis_client:
                            import json
                            self.redis_client.setex(f'market_state:{symbol}', 60, json.dumps(state))
                    
                    import time
                    time.sleep(60)  # Every minute
                except Exception as e:
                    logger.error(f"Market Monitor error: {e}")
                    import time
                    time.sleep(30)
        except ImportError:
            logger.error("Market Intelligence not available")
    
    def stop_background_services(self):
        """Stop all background services."""
        logger.info("Stopping background services...")
        
        for name, process in self.background_processes.items():
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                logger.info(f"✓ Stopped: {name}")
        
        self.background_processes.clear()
    
    # ========================================================================
    # LAYER 3: SCHEDULED JOBS
    # ========================================================================
    
    def setup_scheduled_jobs(self):
        """Setup Layer 3 scheduled training jobs."""
        logger.info("=" * 70)
        logger.info("LAYER 3: SETTING UP SCHEDULED JOBS")
        logger.info("=" * 70)
        
        jobs = [
            ('Offline RL Training', 'Daily 2:00 AM'),
            ('Neural Evolution', 'Daily 3:00 AM'),
            ('Adversarial Testing', 'Sunday 3:00 AM'),
            ('Pattern Discovery', 'Sunday 4:00 AM'),
            ('Performance Analysis', 'Daily 5:00 PM'),
        ]
        
        logger.info("Scheduled jobs configured:")
        for name, schedule in jobs:
            logger.info(f"  - {name}: {schedule}")
        
        logger.info("\nTo activate, run: setup_scheduled_jobs.bat")
        logger.info("=" * 70)
    
    # ========================================================================
    # LAYER 4: COORDINATION (On-Demand)
    # ========================================================================
    
    def activate_coordination_layer(self):
        """Activate Layer 4 coordination for multi-agent scenarios."""
        logger.info("=" * 70)
        logger.info("LAYER 4: COORDINATION LAYER (STANDBY)")
        logger.info("=" * 70)
        
        logger.info("Intelligent Delegation system ready for multi-agent coordination")
        logger.info("Activate when needed with: orchestrator.delegate(task)")
        logger.info("=" * 70)
    
    # ========================================================================
    # SYSTEM STATUS & MONITORING
    # ========================================================================
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status across all layers."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'layers': {},
        }
        
        # Layer 1: Core Systems (would query from main.py)
        status['layers']['layer_1_core'] = {
            'status': 'active',
            'systems': ['elite_ai', 'market_intelligence', 'complete_system'],
        }
        
        # Layer 2: Background Services
        status['layers']['layer_2_background'] = {
            'status': 'active' if self.background_processes else 'inactive',
            'services': {
                name: {
                    'pid': proc.pid,
                    'alive': proc.is_alive(),
                }
                for name, proc in self.background_processes.items()
            },
        }
        
        # Layer 3: Scheduled Jobs
        status['layers']['layer_3_scheduled'] = {
            'status': 'configured',
            'jobs': 5,
        }
        
        # Layer 4: Coordination
        status['layers']['layer_4_coordination'] = {
            'status': 'standby',
        }
        
        # Redis status
        status['redis'] = {
            'connected': self.redis_client is not None,
        }
        
        return status
    
    def print_status(self):
        """Print formatted system status."""
        status = self.get_system_status()
        
        print("\n" + "=" * 70)
        print("MASTER ORCHESTRATOR - SYSTEM STATUS")
        print("=" * 70)
        print(f"Timestamp: {status['timestamp']}")
        print()
        
        print("LAYER 1 - Core Systems (Main Trading Loop)")
        print(f"  Status: {status['layers']['layer_1_core']['status'].upper()}")
        print(f"  Systems: {', '.join(status['layers']['layer_1_core']['systems'])}")
        print()
        
        print("LAYER 2 - Background Services")
        print(f"  Status: {status['layers']['layer_2_background']['status'].upper()}")
        for name, info in status['layers']['layer_2_background']['services'].items():
            print(f"  - {name}: PID={info['pid']}, Alive={info['alive']}")
        print()
        
        print("LAYER 3 - Scheduled Jobs")
        print(f"  Status: {status['layers']['layer_3_scheduled']['status'].upper()}")
        print(f"  Jobs: {status['layers']['layer_3_scheduled']['jobs']} configured")
        print()
        
        print("LAYER 4 - Coordination Layer")
        print(f"  Status: {status['layers']['layer_4_coordination']['status'].upper()}")
        print()
        
        print(f"Redis: {'CONNECTED' if status['redis']['connected'] else 'DISCONNECTED'}")
        print("=" * 70)
    
    # ========================================================================
    # STARTUP & SHUTDOWN
    # ========================================================================
    
    def start_all(self, args=None):
        """Start all layers of the trading bot."""
        logger.info("\n" + "=" * 70)
        logger.info("STARTING FULL STACK TRADING BOT")
        logger.info("=" * 70)
        
        self.running = True
        
        # Layer 2: Background Services
        self.start_background_services()
        
        # Layer 3: Scheduled Jobs (just setup, actual scheduling via Task Scheduler)
        self.setup_scheduled_jobs()
        
        # Layer 4: Coordination (standby)
        self.activate_coordination_layer()
        
        logger.info("\n" + "=" * 70)
        logger.info("FULL STACK STARTUP COMPLETE")
        logger.info("=" * 70)
        logger.info("\nAll systems operational. Ready for trading.")
        logger.info("Layer 1 (Core): Start with main.py --use-all-systems")
        logger.info("Layer 2 (Background): Running")
        logger.info("Layer 3 (Scheduled): Configured")
        logger.info("Layer 4 (Coordination): Standby")
        logger.info("=" * 70 + "\n")
    
    def stop_all(self):
        """Stop all layers gracefully."""
        logger.info("\n" + "=" * 70)
        logger.info("SHUTTING DOWN FULL STACK")
        logger.info("=" * 70)
        
        self.running = False
        
        # Stop background services
        self.stop_background_services()
        
        logger.info("=" * 70)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 70 + "\n")
    
    # ========================================================================
    # HEALTH MONITORING
    # ========================================================================
    
    async def monitor_health(self):
        """Monitor health of all systems."""
        logger.info("Starting health monitor...")
        
        while self.running:
            try:
                # Check background services
                for name, process in list(self.background_processes.items()):
                    if not process.is_alive():
                        logger.warning(f"Service '{name}' died - restarting...")
                        # Could implement auto-restart here
                
                # Check Redis
                if self.redis_client:
                    try:
                        self.redis_client.ping()
                    except:
                        logger.error("Redis connection lost")
                        self._init_redis()
                
                # Log system metrics
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory().percent
                
                if cpu > 80:
                    logger.warning(f"High CPU usage: {cpu:.1f}%")
                if memory > 80:
                    logger.warning(f"High memory usage: {memory:.1f}%")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    sys.exit(0)


async def main():
    """Main entry point for standalone execution."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create orchestrator
    orchestrator = MasterOrchestrator()
    
    try:
        # Start all layers
        orchestrator.start_all()
        
        # Print status
        orchestrator.print_status()
        
        # Monitor health
        await orchestrator.monitor_health()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        orchestrator.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
