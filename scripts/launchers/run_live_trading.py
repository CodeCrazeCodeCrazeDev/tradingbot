#!/usr/bin/env python
"""
Live Trading Runner

Run the trading bot in LIVE mode with REAL MONEY.

⚠️  WARNING: This script trades with REAL MONEY!
⚠️  Only use after successful paper trading validation!
⚠️  Start with Stage 1 (minimal capital) and scale up gradually!

Usage:
    python run_live_trading.py --stage 1
    python run_live_trading.py --stage 2 --symbol EURUSD
    python run_live_trading.py --check-only
"""

import asyncio
import argparse
import sys
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from trading_bot.validation.paper_trading_validator import (
    PaperTradingValidator,
    LiveTradingGate,
    ValidationThresholds
)
from trading_bot.brokers.broker_adapter import MT5BrokerAdapter, MockBrokerAdapter
from trading_bot.monitoring.live_monitor import LiveMonitor, TradeEvent


# Capital stages for progressive scaling
CAPITAL_STAGES = {
    1: {
        'name': 'Stage 1 - Validation',
        'capital': 100.0,
        'max_risk_per_trade': 0.005,  # 0.5%
        'max_daily_loss': 0.02,  # 2%
        'max_positions': 1,
        'description': 'Initial live validation with minimal capital'
    },
    2: {
        'name': 'Stage 2 - Confirmation',
        'capital': 250.0,
        'max_risk_per_trade': 0.005,
        'max_daily_loss': 0.02,
        'max_positions': 2,
        'description': 'Confirming strategy works in live conditions'
    },
    3: {
        'name': 'Stage 3 - Scaling',
        'capital': 500.0,
        'max_risk_per_trade': 0.01,  # 1%
        'max_daily_loss': 0.03,  # 3%
        'max_positions': 2,
        'description': 'Scaling up with proven performance'
    },
    4: {
        'name': 'Stage 4 - Full',
        'capital': 1000.0,
        'max_risk_per_trade': 0.01,
        'max_daily_loss': 0.03,
        'max_positions': 3,
        'description': 'Full capital deployment'
    }
}


class LiveTradingRunner:
    """
    Live Trading Runner with Safety Controls
    
    Features:
    - Progressive capital scaling
    - Strict risk limits
    - Real-time monitoring
    - Emergency stop functionality
    - Comprehensive logging
    """
    
    def __init__(
        self,
        stage: int = 1,
        symbol: str = "EURUSD",
        config_path: str = "config/live_trading_config.yaml",
        dry_run: bool = False
    ):
        self.stage = stage
        self.symbol = symbol
        self.config_path = config_path
        self.dry_run = dry_run
        
        # Get stage configuration
        self.stage_config = CAPITAL_STAGES.get(stage, CAPITAL_STAGES[1])
        self.capital = self.stage_config['capital']
        
        # Initialize components
        self.broker = None
        self.monitor = None
        self.validator = None
        
        self.is_running = False
        self.emergency_stop = False
        
        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.open_positions = 0
        
        logger.info(f"Live Trading Runner initialized")
        logger.info(f"  Stage: {stage} - {self.stage_config['name']}")
        logger.info(f"  Capital: ${self.capital:,.2f}")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Dry Run: {dry_run}")
    
    async def pre_flight_check(self) -> bool:
        """
        Run pre-flight checks before starting live trading.
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("")
        print("=" * 60)
        print("PRE-FLIGHT CHECKS")
        print("=" * 60)
        
        checks_passed = True
        
        # 1. Paper trading validation
        print("\n1. Checking paper trading validation...")
        self.validator = PaperTradingValidator(data_dir="data/paper_trading")
        if self.validator.load_state():
            result = self.validator.validate()
            if result.ready_for_live:
                print("   ✓ Paper trading validation PASSED")
            else:
                print("   ✗ Paper trading validation FAILED")
                print(f"     Status: {result.status.value}")
                for check in result.failed_checks:
                    print(f"     - {check}")
                checks_passed = False
        else:
            print("   ✗ No paper trading data found")
            print("     Run paper trading first: python run_paper_trading.py")
            checks_passed = False
        
        # 2. Configuration check
        print("\n2. Checking configuration...")
        if os.path.exists(self.config_path):
            print(f"   ✓ Configuration file exists: {self.config_path}")
        else:
            print(f"   ✗ Configuration file not found: {self.config_path}")
            checks_passed = False
        
        # 3. Broker connection check
        print("\n3. Checking broker connection...")
        if self.dry_run:
            print("   ✓ Dry run mode - using mock broker")
            self.broker = MockBrokerAdapter({'initial_balance': self.capital})
        else:
            try:
                self.broker = MT5BrokerAdapter({
                    'login': os.getenv('MT5_LOGIN'),
                    'password': os.getenv('MT5_PASSWORD'),
                    'server': os.getenv('MT5_SERVER')
                })
                if await self.broker.connect():
                    print("   ✓ Broker connection successful")
                    account_info = await self.broker.get_account_info()
                    print(f"     Balance: ${account_info.get('balance', 0):,.2f}")
                    print(f"     Equity: ${account_info.get('equity', 0):,.2f}")
                else:
                    print("   ✗ Broker connection failed")
                    checks_passed = False
            except Exception as e:
                print(f"   ✗ Broker connection error: {e}")
                checks_passed = False
        
        # 4. Capital check
        print("\n4. Checking capital limits...")
        print(f"   Stage {self.stage} capital limit: ${self.capital:,.2f}")
        if self.broker:
            try:
                equity = await self.broker.get_account_equity()
                if equity >= self.capital:
                    print(f"   ✓ Sufficient capital available: ${equity:,.2f}")
                else:
                    print(f"   ⚠ Available capital (${equity:,.2f}) less than stage limit")
            except:
                pass
        
        # 5. Risk limits check
        print("\n5. Checking risk limits...")
        print(f"   Max risk per trade: {self.stage_config['max_risk_per_trade']:.1%}")
        print(f"   Max daily loss: {self.stage_config['max_daily_loss']:.1%}")
        print(f"   Max positions: {self.stage_config['max_positions']}")
        print("   ✓ Risk limits configured")
        
        # 6. Emergency contacts check
        print("\n6. Checking emergency contacts...")
        if os.getenv('ALERT_EMAIL'):
            print(f"   ✓ Alert email configured")
        else:
            print("   ⚠ No alert email configured (recommended)")
        
        # Summary
        print("")
        print("=" * 60)
        if checks_passed:
            print("✓ ALL PRE-FLIGHT CHECKS PASSED")
        else:
            print("✗ SOME PRE-FLIGHT CHECKS FAILED")
            print("  Fix the issues above before proceeding.")
        print("=" * 60)
        
        return checks_passed
    
    async def start(self) -> bool:
        """Start live trading"""
        # Run pre-flight checks
        if not await self.pre_flight_check():
            logger.error("Pre-flight checks failed. Cannot start live trading.")
            return False
        
        # Confirm with user
        if not self.dry_run:
            print("")
            print("⚠️  WARNING: You are about to start LIVE TRADING with REAL MONEY!")
            print(f"   Stage: {self.stage} - {self.stage_config['name']}")
            print(f"   Capital at risk: ${self.capital:,.2f}")
            print("")
            
            confirm = input("Type 'START LIVE' to confirm: ")
            if confirm != "START LIVE":
                print("Live trading cancelled.")
                return False
        
        # Initialize monitor
        self.monitor = LiveMonitor({
            'max_daily_loss': self.stage_config['max_daily_loss'],
            'max_drawdown': 0.10,
            'max_daily_trades': 10,
            'monitor_interval': 30
        })
        
        # Start monitoring
        self.monitor.start()
        
        self.is_running = True
        
        logger.info("=" * 60)
        logger.info("LIVE TRADING STARTED")
        logger.info("=" * 60)
        logger.info(f"Stage: {self.stage} - {self.stage_config['name']}")
        logger.info(f"Capital: ${self.capital:,.2f}")
        logger.info(f"Symbol: {self.symbol}")
        logger.info("")
        logger.info("Press Ctrl+C to stop trading safely.")
        
        return True
    
    async def stop(self):
        """Stop live trading safely"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STOPPING LIVE TRADING")
        logger.info("=" * 60)
        
        self.is_running = False
        
        # Close all positions if emergency
        if self.emergency_stop:
            logger.warning("Emergency stop - closing all positions...")
            await self._close_all_positions()
        
        # Stop monitor
        if self.monitor:
            self.monitor.stop()
        
        # Disconnect broker
        if self.broker:
            await self.broker.disconnect()
        
        # Print final summary
        self._print_summary()
    
    async def _close_all_positions(self):
        """Close all open positions"""
        if not self.broker:
            return
        
        try:
            positions = await self.broker.get_positions()
            for pos in positions:
                logger.info(f"Closing position: {pos.symbol}")
                if hasattr(self.broker, 'close_position'):
                    await self.broker.close_position(pos.symbol)
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def _print_summary(self):
        """Print trading session summary"""
        print("")
        print("=" * 60)
        print("LIVE TRADING SESSION SUMMARY")
        print("=" * 60)
        print(f"Stage: {self.stage} - {self.stage_config['name']}")
        print(f"Capital: ${self.capital:,.2f}")
        print(f"Daily Trades: {self.daily_trades}")
        print(f"Daily P&L: ${self.daily_pnl:,.2f}")
        print(f"Total P&L: ${self.total_pnl:,.2f}")
        
        if self.monitor:
            status = self.monitor.get_status()
            print(f"Win Rate: {status['win_rate']:.1%}")
            print(f"Drawdown: {status['current_drawdown']:.1%}")
            print(f"Errors: {status['errors_count']}")
        
        print("=" * 60)
    
    def trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop"""
        logger.critical(f"EMERGENCY STOP: {reason}")
        self.emergency_stop = True
        self.is_running = False


async def check_readiness():
    """Check if ready for live trading"""
    print("")
    print("=" * 60)
    print("LIVE TRADING READINESS CHECK")
    print("=" * 60)
    
    validator = PaperTradingValidator(data_dir="data/paper_trading")
    
    if not validator.load_state():
        print("")
        print("✗ No paper trading data found!")
        print("")
        print("You must complete paper trading validation first.")
        print("Run: python run_paper_trading.py --demo 50")
        print("")
        return
    
    gate = LiveTradingGate(validator)
    is_ready, passed, failed = gate.check_readiness()
    
    print("\nPassed Checks:")
    for check in passed:
        print(f"  ✓ {check}")
    
    if failed:
        print("\nFailed Checks:")
        for check in failed:
            print(f"  ✗ {check}")
    
    stage = gate.get_capital_stage()
    
    print(f"\nRecommended Stage: {stage['name']}")
    print(f"  Capital: ${stage['capital']:,.2f}")
    print(f"  Qualified: {'YES' if stage.get('qualified', False) else 'NO'}")
    
    if is_ready:
        print("\n" + "=" * 60)
        print("✓ READY FOR LIVE TRADING")
        print("=" * 60)
        print("\nTo start live trading:")
        print("  python run_live_trading.py --stage 1")
        print("\nTo do a dry run first:")
        print("  python run_live_trading.py --stage 1 --dry-run")
    else:
        print("\n" + "=" * 60)
        print("✗ NOT READY FOR LIVE TRADING")
        print("=" * 60)
        print("\nContinue paper trading to meet requirements.")
        print("Run: python run_paper_trading.py")
    
    print("")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Live Trading Runner - Trade with REAL MONEY"
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help="Capital stage (1-4, default: 1)"
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD",
        help="Trading symbol (default: EURUSD)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (uses mock broker)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check readiness, don't start trading"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip paper trading validation (DANGEROUS!)"
    )
    
    args = parser.parse_args()
    
    # Check-only mode
    if args.check_only:
        await check_readiness()
        return
    
    # Create runner
    runner = LiveTradingRunner(
        stage=args.stage,
        symbol=args.symbol,
        dry_run=args.dry_run
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received...")
        runner.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading
    if not await runner.start():
        return
    
    # Main loop
    try:
        while runner.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await runner.stop()


if __name__ == "__main__":
    print("")
    print("=" * 60)
    print("⚠️  ALPHAALGO LIVE TRADING SYSTEM ⚠️")
    print("=" * 60)
    print("")
    print("This system trades with REAL MONEY!")
    print("Make sure you have:")
    print("  1. Completed paper trading validation")
    print("  2. Configured broker credentials")
    print("  3. Set appropriate risk limits")
    print("  4. Understood all risks involved")
    print("")
    
    asyncio.run(main())
