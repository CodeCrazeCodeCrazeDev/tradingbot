"""
Operational Trading Bot Runner with Continuous Monitoring
==========================================================
This script runs the trading bot in full operational mode with:
- Continuous health monitoring
- Automatic error recovery
- Performance tracking
- Real-time alerting
- Graceful shutdown handling

Author: AI Trading Systems Engineer
Date: 2025-10-08
"""

import asyncio
import json
import logging
import os
import sys
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/operational_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OperationalMetrics:
    """Tracks operational metrics."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.trades_executed = 0
        self.signals_generated = 0
        self.errors_encountered = 0
        self.health_checks_performed = 0
        self.last_health_check = None
        self.uptime_seconds = 0
        self.performance_data = []
        
    def update_uptime(self):
        """Update uptime."""
        self.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
    
    def record_trade(self):
        """Record a trade execution."""
        self.trades_executed += 1
    
    def record_signal(self):
        """Record a signal generation."""
        self.signals_generated += 1
    
    def record_error(self):
        """Record an error."""
        self.errors_encountered += 1
    
    def record_health_check(self):
        """Record a health check."""
        self.health_checks_performed += 1
        self.last_health_check = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        self.update_uptime()
        return {
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': self.uptime_seconds,
            'uptime_formatted': str(timedelta(seconds=int(self.uptime_seconds))),
            'trades_executed': self.trades_executed,
            'signals_generated': self.signals_generated,
            'errors_encountered': self.errors_encountered,
            'health_checks_performed': self.health_checks_performed,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'error_rate': round(self.errors_encountered / max(1, self.trades_executed) * 100, 2)
        }


class HealthMonitor:
    """Continuous health monitoring system."""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.health_history = []
        self.alert_thresholds = {
            'cpu_percent': 90,
            'memory_percent': 90,
            'error_rate': 10,
            'response_time_ms': 5000
        }
        
    async def start(self):
        """Start health monitoring."""
        self.running = True
        logger.info(f"Health monitoring started (interval: {self.check_interval}s)")
        
        while self.running:
            try:
                health_status = await self.check_health()
                self.health_history.append(health_status)
                
                # Keep only last 1000 checks
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]
                
                # Check for alerts
                await self.check_alerts(health_status)
                
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        timestamp = datetime.now()
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # Process check
        bot_process = self._find_bot_process()
        
        health_status = {
            'timestamp': timestamp.isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'bot_running': bot_process is not None,
            'bot_pid': bot_process.pid if bot_process else None,
            'bot_memory_mb': round(bot_process.memory_info().rss / (1024**2), 2) if bot_process else 0,
            'bot_cpu_percent': bot_process.cpu_percent() if bot_process else 0
        }
        
        # Log health status
        status_emoji = '✅' if health_status['bot_running'] else '❌'
        logger.info(
            f"{status_emoji} Health | CPU: {cpu_percent:.1f}% | "
            f"Mem: {memory.percent:.1f}% | "
            f"Bot: {'Running' if bot_process else 'Stopped'} | "
            f"Bot Mem: {health_status['bot_memory_mb']:.1f}MB"
        )
        
        return health_status
    
    def _find_bot_process(self):
        """Find the trading bot process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if any('main.py' in str(arg) for arg in cmdline):
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    async def check_alerts(self, health_status: Dict[str, Any]):
        """Check for alert conditions."""
        alerts = []
        
        if health_status['cpu_percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append(f"⚠️ HIGH CPU: {health_status['cpu_percent']:.1f}%")
        
        if health_status['memory_percent'] > self.alert_thresholds['memory_percent']:
            alerts.append(f"⚠️ HIGH MEMORY: {health_status['memory_percent']:.1f}%")
        
        if health_status['disk_percent'] > 90:
            alerts.append(f"⚠️ LOW DISK SPACE: {health_status['disk_free_gb']:.1f}GB free")
        
        if not health_status['bot_running']:
            alerts.append("🚨 BOT NOT RUNNING!")
        
        if alerts:
            for alert in alerts:
                logger.warning(alert)
    
    def stop(self):
        """Stop health monitoring."""
        self.running = False
        logger.info("Health monitoring stopped")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        if not self.health_history:
            return {'status': 'No health data available'}
        
        recent_checks = self.health_history[-10:]
        
        avg_cpu = sum(h['cpu_percent'] for h in recent_checks) / len(recent_checks)
        avg_memory = sum(h['memory_percent'] for h in recent_checks) / len(recent_checks)
        bot_uptime = sum(1 for h in recent_checks if h['bot_running']) / len(recent_checks) * 100
        
        return {
            'total_checks': len(self.health_history),
            'recent_avg_cpu': round(avg_cpu, 2),
            'recent_avg_memory': round(avg_memory, 2),
            'bot_uptime_percent': round(bot_uptime, 2),
            'last_check': recent_checks[-1] if recent_checks else None
        }


class TradingBotOperator:
    """Main operational trading bot controller."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = OperationalMetrics()
        self.health_monitor = HealthMonitor(check_interval=60)
        self.running = False
        self.mt5_interface = None
        self.strategy_engine = None
        self.risk_manager = None
        self.executor = None
        
    async def initialize(self):
        """Initialize trading bot components."""
        logger.info("Initializing trading bot components...")
        
        try:
            from trading_bot.data import MT5Interface
            from trading_bot.strategy import StrategyEngine, MLStrategyEngine
            from trading_bot.risk import RiskManager
            from trading_bot.execution import PaperExecutor, LiveExecutor
            
            # Initialize MT5
            self.mt5_interface = MT5Interface()
            if not self.mt5_interface.initialize():
                raise Exception("Failed to initialize MT5")
            
            # Get account info
            account_info = self.mt5_interface.account_info()
            if account_info:
                logger.info(f"Connected to MT5 - Account: {account_info.login}, Balance: {account_info.balance}")
            
            # Initialize strategy engine
            symbol = self.config.get('symbol', 'EURUSD')
            use_ml = self.config.get('use_ml', False)
            
            if use_ml:
                self.strategy_engine = MLStrategyEngine(
                    self.mt5_interface,
                    symbol=symbol,
                    use_price_prediction=True,
                    use_pattern_recognition=True,
                    use_sentiment=self.config.get('use_sentiment', False)
                )
                logger.info("ML Strategy Engine initialized")
            else:
                self.strategy_engine = StrategyEngine(self.mt5_interface, symbol=symbol)
                logger.info("Traditional Strategy Engine initialized")
            
            # Initialize risk manager
            self.risk_manager = RiskManager(self.mt5_interface)
            logger.info("Risk Manager initialized")
            
            # Initialize executor
            mode = self.config.get('mode', 'paper')
            if mode == 'live':
                self.executor = LiveExecutor(self.mt5_interface, self.risk_manager)
                logger.warning("⚠️ LIVE TRADING MODE ENABLED - Real orders will be placed!")
            else:
                self.executor = PaperExecutor(self.mt5_interface, self.risk_manager)
                logger.info("Paper Trading Mode - No real orders will be placed")
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def run_trading_cycle(self):
        """Run a single trading cycle."""
        try:
            symbol = self.config.get('symbol', 'EURUSD')
            timeframe = self.config.get('timeframe', 'H1')
            bars = self.config.get('bars', 200)
            
            # Get market data
            rates = self.mt5_interface.get_rates(symbol, timeframe, bars)
            if not rates or len(rates) == 0:
                logger.warning("No market data available")
                return
            
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(rates)
            df.set_index('time', inplace=True)
            
            # Generate signals
            if hasattr(self.strategy_engine, 'generate_signals'):
                signals = await self.strategy_engine.generate_signals()
            else:
                signals = self.strategy_engine.analyse(df)
            
            if signals:
                self.metrics.record_signal()
                logger.info(f"Signal generated: {signals}")
                
                # Process signals
                if isinstance(signals, dict):
                    signals = [signals]
                
                for signal in signals:
                    # Calculate position size
                    stop_loss_pips = signal.get('stop_loss_pips', 20)
                    
                    try:
                        position_size = self.risk_manager.calculate_position_size(
                            symbol=symbol,
                            stop_loss_pips=stop_loss_pips
                        )
                        
                        if hasattr(position_size, 'lot'):
                            lot_size = position_size.lot
                        else:
                            lot_size = position_size
                        
                        if lot_size > 0:
                            # Execute trade
                            direction = signal.get('direction', 1)
                            result = await self.executor.execute_trade(
                                symbol=symbol,
                                direction=direction,
                                size=lot_size
                            )
                            
                            self.metrics.record_trade()
                            logger.info(f"Trade executed: {result}")
                    
                    except Exception as e:
                        logger.error(f"Error executing trade: {e}")
                        self.metrics.record_error()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            self.metrics.record_error()
    
    async def run(self):
        """Run the trading bot in operational mode."""
        self.running = True
        logger.info("=" * 80)
        logger.info("TRADING BOT OPERATIONAL MODE")
        logger.info("=" * 80)
        logger.info(f"Started at: {datetime.now()}")
        logger.info(f"Symbol: {self.config.get('symbol', 'EURUSD')}")
        logger.info(f"Timeframe: {self.config.get('timeframe', 'H1')}")
        logger.info(f"Mode: {self.config.get('mode', 'paper').upper()}")
        logger.info("=" * 80)
        
        # Initialize components
        if not await self.initialize():
            logger.error("Failed to initialize - aborting")
            return
        
        # Start health monitoring
        health_task = asyncio.create_task(self.health_monitor.start())
        
        # Main trading loop
        cycle_interval = self.config.get('cycle_interval', 60)
        
        try:
            while self.running:
                try:
                    # Run trading cycle
                    await self.run_trading_cycle()
                    
                    # Update metrics
                    self.metrics.update_uptime()
                    
                    # Log status every 10 cycles
                    if self.metrics.signals_generated % 10 == 0 and self.metrics.signals_generated > 0:
                        self.log_status()
                    
                    # Wait for next cycle
                    await asyncio.sleep(cycle_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Shutdown requested by user")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    logger.error(traceback.format_exc())
                    self.metrics.record_error()
                    await asyncio.sleep(cycle_interval)
        
        finally:
            # Cleanup
            await self.shutdown()
            health_task.cancel()
    
    def log_status(self):
        """Log current status."""
        metrics = self.metrics.get_summary()
        health = self.health_monitor.get_health_summary()
        
        logger.info("=" * 80)
        logger.info("OPERATIONAL STATUS")
        logger.info("-" * 80)
        logger.info(f"Uptime: {metrics['uptime_formatted']}")
        logger.info(f"Signals Generated: {metrics['signals_generated']}")
        logger.info(f"Trades Executed: {metrics['trades_executed']}")
        logger.info(f"Errors: {metrics['errors_encountered']} ({metrics['error_rate']:.2f}%)")
        logger.info(f"Health Checks: {metrics['health_checks_performed']}")
        logger.info("-" * 80)
        logger.info(f"Avg CPU: {health.get('recent_avg_cpu', 0):.1f}%")
        logger.info(f"Avg Memory: {health.get('recent_avg_memory', 0):.1f}%")
        logger.info(f"Bot Uptime: {health.get('bot_uptime_percent', 0):.1f}%")
        logger.info("=" * 80)
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        
        self.running = False
        self.health_monitor.stop()
        
        # Close MT5 connection
        if self.mt5_interface:
            self.mt5_interface.shutdown()
            logger.info("MT5 connection closed")
        
        # Save final metrics
        metrics = self.metrics.get_summary()
        health = self.health_monitor.get_health_summary()
        
        report = {
            'shutdown_time': datetime.now().isoformat(),
            'metrics': metrics,
            'health': health
        }
        
        # Save report
        report_path = f'logs/operational_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Final report saved to: {report_path}")
        logger.info("Shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Operational Trading Bot Runner')
    parser.add_argument('--symbol', default='EURUSD', help='Trading symbol')
    parser.add_argument('--timeframe', default='H1', help='Timeframe')
    parser.add_argument('--bars', type=int, default=200, help='Number of bars')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper', help='Trading mode')
    parser.add_argument('--use-ml', action='store_true', help='Use ML strategy')
    parser.add_argument('--use-sentiment', action='store_true', help='Use sentiment analysis')
    parser.add_argument('--cycle-interval', type=int, default=60, help='Cycle interval in seconds')
    
    args = parser.parse_args()
    
    # Create config
    config = {
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'bars': args.bars,
        'mode': args.mode,
        'use_ml': args.use_ml,
        'use_sentiment': args.use_sentiment,
        'cycle_interval': args.cycle_interval
    }
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run operator
    operator = TradingBotOperator(config)
    
    try:
        await operator.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await operator.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
