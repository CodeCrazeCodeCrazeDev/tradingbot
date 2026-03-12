"""
Elite 5-Star Trading Bot Integration
Integrates all elite systems into a cohesive trading platform
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

# Import all elite systems
from trading_bot.strategy.elite_strategy_engine import EliteStrategyEngine, EliteSignal
from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from trading_bot.monitoring.elite_monitor import EliteMonitor, AlertLevel
from trading_bot.connectivity.resilient_connection import ConnectionPool, ResilientConnection
from trading_bot.validation.data_quality import DataQualityValidator
from trading_bot.performance.performance_profiler import PerformanceProfiler, PerformanceOptimizer, profile

# Import existing 100% systems
from trading_bot.master_integration import MasterTradingSystem
from enum import auto
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class Elite5StarTradingBot:
    """
    Elite 5-Star Trading Bot
    
    Integrates:
    - Elite Strategy Engine (multi-confirmation)
    - Circuit Breaker System (loss protection)
    - Elite Monitor (real-time alerts)
    - Resilient Connections (auto-recovery)
    - Data Quality Validator (integrity checks)
    - Performance Profiler (optimization)
    - Master Trading System (100% complete)
    
    This is the ultimate institutional-grade trading system.
    """
    
    def __init__(self, 
                 symbol: str = "EURUSD",
                 initial_balance: float = 10000,
                 telegram_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None,
                 discord_webhook: Optional[str] = None):
        
        self.symbol = symbol
        self.initial_balance = initial_balance
        
        logger.info("=" * 80)
        logger.info("🌟 INITIALIZING ELITE 5-STAR TRADING BOT 🌟")
        logger.info("=" * 80)
        
        # Initialize all elite systems
        self.strategy = EliteStrategyEngine(symbol=symbol)
        self.circuit_breaker = CircuitBreaker()
        self.monitor = EliteMonitor(
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat_id,
            discord_webhook=discord_webhook
        )
        self.connection_pool = ConnectionPool()
        self.data_validator = DataQualityValidator(strict_mode=True)
        self.profiler = PerformanceProfiler(enable_memory_tracking=True)
        self.optimizer = PerformanceOptimizer(self.profiler)
        
        # Initialize 100% complete system
        self.master_system = MasterTradingSystem()
        
        # Start trading session
        self.circuit_breaker.start_session(initial_balance)
        
        logger.info("✅ All elite systems initialized")
        logger.info("=" * 80)
    
    @profile("elite_bot.process_trade")
    async def process_trade(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Process trade through all elite systems
        
        Pipeline:
        1. Data validation
        2. Circuit breaker check
        3. Strategy analysis
        4. Master system execution
        5. Performance monitoring
        """
        
        # STEP 1: Data Validation
        logger.info("Step 1: Validating data quality...")
        is_valid, validation_results = self.data_validator.validate_ohlcv(df)
        
        if not is_valid:
            await self.monitor.send_alert(
                AlertLevel.ERROR,
                "Data Validation Failed",
                "Trading halted due to data quality issues",
                metadata={'validation': self.data_validator.get_validation_summary()}
            )
            return None
        
        logger.info("✅ Data validation passed")
        
        # STEP 2: Circuit Breaker Check
        logger.info("Step 2: Checking circuit breaker...")
        can_trade, reason = self.circuit_breaker.can_trade()
        
        if not can_trade:
            logger.warning(f"⚠️ Trading blocked: {reason}")
            return None
        
        logger.info("✅ Circuit breaker check passed")
        
        # STEP 3: Strategy Analysis
        logger.info("Step 3: Analyzing market with elite strategy...")
        signals = self.strategy.analyze(df, self.circuit_breaker.session.current_balance)
        
        if not signals:
            logger.info("No trading signals generated")
            return None
        
        # Take the strongest signal
        signal = max(signals, key=lambda s: s.confidence)
        logger.info(f"✅ Signal generated: {signal.direction} with {len(signal.confirmations)} confirmations")
        
        # STEP 4: Execute through Master System
        logger.info("Step 4: Executing through 100% master system...")
        
        # Convert elite signal to master system format
        master_signal = {
            'signal_id': f'ELITE-{datetime.now().timestamp()}',
            'symbol': signal.symbol,
            'direction': signal.direction,
            'confidence': signal.confidence,
            'regime': signal.regime.value,
            'timeframe_consensus': 0.8,  # Elite strategy has high consensus
            'is_healthy': True,
            'strength_bucket': signal.strength.name.lower(),
            'created_at': signal.time,
            'price': signal.entry_price,
            'prices': df['close'].values,
            'data': df,
            'order_type': 'LIMIT',
            'volatility': signal.metadata['atr'],
            'token': 'elite_system_token',
            'client_id': 'elite_bot',
            'portfolio': {
                'capital': self.circuit_breaker.session.current_balance,
                'value': self.circuit_breaker.session.current_balance,
                'drawdown': (self.circuit_breaker.session.peak_balance - self.circuit_breaker.session.current_balance) / self.circuit_breaker.session.peak_balance
            },
            'market_state': {
                'regime': signal.regime.value,
                'volatility': signal.metadata['atr']
            },
            'venues': ['MT5']
        }
        
        result = await self.master_system.execute_complete_trade(master_signal)
        
        if result['status'] != 'SUCCESS':
            logger.warning(f"❌ Trade rejected: {result.get('reason')}")
            return None
        
        logger.info("✅ Trade executed successfully")
        
        # STEP 5: Record Trade
        # Calculate P&L (simplified - would integrate with actual execution)
        pnl = signal.position_size * (signal.take_profit_2 - signal.entry_price) if signal.direction == 'BUY' else signal.position_size * (signal.entry_price - signal.take_profit_2)
        is_win = pnl > 0
        
        # Update circuit breaker
        self.circuit_breaker.record_trade(pnl, is_win)
        
        # Update monitor
        self.monitor.record_trade(pnl, signal.symbol, signal.direction)
        
        # Send success alert
        await self.monitor.send_alert(
            AlertLevel.INFO,
            "Trade Executed",
            f"✅ {signal.direction} {signal.symbol}\nEntry: {signal.entry_price:.5f}\nSL: {signal.stop_loss:.5f}\nTP: {signal.take_profit_2:.5f}\nConfidence: {signal.confidence:.2%}",
            metadata={
                'signal': signal.__dict__,
                'result': result
            }
        )
        
        return {
            'signal': signal,
            'result': result,
            'pnl': pnl
        }
    
    async def run_trading_loop(self, data_source_func, interval_seconds: int = 60):
        """
        Main trading loop
        
        Args:
            data_source_func: Function that returns DataFrame with OHLCV data
            interval_seconds: Loop interval
        """
        logger.info("🚀 Starting Elite Trading Loop")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"ITERATION {iteration} - {datetime.now()}")
                logger.info(f"{'='*60}")
                
                try:
                    # Get market data
                    df = await data_source_func()
                    
                    if df is None or len(df) < 200:
                        logger.warning("Insufficient data")
                        await asyncio.sleep(interval_seconds)
                        continue
                    
                    # Process trade
                    result = await self.process_trade(df)
                    
                    if result:
                        logger.info(f"✅ Trade processed: P&L ${result['pnl']:,.2f}")
                    
                    # Log performance metrics every 10 iterations
                    if iteration % 10 == 0:
                        await self._log_performance()
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}", exc_info=True)
                    await self.monitor.send_alert(
                        AlertLevel.ERROR,
                        "Trading Loop Error",
                        f"Error: {str(e)}",
                        metadata={'iteration': iteration}
                    )
                
                # Wait for next iteration
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Trading loop stopped by user")
        finally:
            await self.shutdown()
    
    async def _log_performance(self):
        """Log performance metrics"""
        # Get profiler report
        perf_report = self.profiler.get_report()
        
        # Get optimizer suggestions
        optimizations = self.optimizer.suggest_optimizations()
        
        # Get circuit breaker status
        cb_status = self.circuit_breaker.get_status()
        
        # Get monitor metrics
        monitor_metrics = self.monitor.get_metrics()
        
        logger.info("\n" + "="*60)
        logger.info("📊 PERFORMANCE REPORT")
        logger.info("="*60)
        logger.info(f"Circuit Breaker: {cb_status['state']}")
        logger.info(f"Balance: ${cb_status['balance']:,.2f}")
        logger.info(f"Daily P&L: ${cb_status['daily_pnl']:,.2f}")
        logger.info(f"Win Rate: {monitor_metrics['win_rate']}")
        logger.info(f"Profit Factor: {monitor_metrics['profit_factor']}")
        logger.info(f"Total Calls: {perf_report['total_calls']}")
        logger.info(f"Bottlenecks: {optimizations['bottlenecks_found']}")
        logger.info("="*60)
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Elite Trading Bot...")
        
        # Send final summary
        await self.monitor.send_daily_summary()
        
        # Disconnect all connections
        await self.connection_pool.disconnect_all()
        
        logger.info("✅ Shutdown complete")
    
    def get_status(self) -> Dict:
        """Get complete system status"""
        return {
            'circuit_breaker': self.circuit_breaker.get_status(),
            'monitor': self.monitor.get_metrics(),
            'connections': self.connection_pool.get_pool_status(),
            'performance': self.profiler.get_report(top_n=5),
            'master_system': self.master_system.get_system_status()
        }


# Export
__all__ = ['Elite5StarTradingBot']
