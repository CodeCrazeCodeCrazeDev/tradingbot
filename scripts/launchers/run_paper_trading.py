#!/usr/bin/env python
"""
Paper Trading Runner

Run the trading bot in paper trading mode for validation before going live.
This script provides a comprehensive paper trading environment with:
- Realistic simulation (slippage, spreads, latency)
- Performance tracking and validation
- Automatic report generation
- Progress towards live trading readiness

Usage:
    python run_paper_trading.py
    python run_paper_trading.py --symbol EURUSD --capital 10000
    python run_paper_trading.py --validate-only
"""

import asyncio
import argparse
import sys
import os
import signal
from datetime import datetime
from pathlib import Path

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
    ValidationThresholds,
    ValidationStatus
)
from trading_bot.brokers.broker_adapter import MockBrokerAdapter, OrderSide, OrderType


class PaperTradingRunner:
    """
    Paper Trading Runner
    
    Runs the trading bot in paper mode with full validation tracking.
    """
    
    def __init__(
        self,
        symbol: str = "EURUSD",
        initial_capital: float = 10000.0,
        config_path: str = "config/paper_trading_config.yaml"
    ):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.config_path = config_path
        
        # Initialize components
        self.validator = PaperTradingValidator(
            initial_capital=initial_capital,
            thresholds=ValidationThresholds(
                min_win_rate=0.45,
                min_profit_factor=1.2,
                max_drawdown=0.15,
                min_sharpe_ratio=0.5,
                max_consecutive_losses=8,
                min_avg_rr_ratio=1.5,
                min_trades=50,
                min_days=7
            ),
            data_dir="data/paper_trading"
        )
        
        self.broker = MockBrokerAdapter({
            'initial_balance': initial_capital,
            'slippage_bps': 2.0
        })
        
        self.gate = LiveTradingGate(self.validator)
        
        self.is_running = False
        self.trade_count = 0
        
        logger.info(f"Paper Trading Runner initialized")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Capital: ${initial_capital:,.2f}")
    
    async def start(self):
        """Start paper trading"""
        logger.info("=" * 60)
        logger.info("STARTING PAPER TRADING SESSION")
        logger.info("=" * 60)
        
        # Load previous state if exists
        self.validator.load_state()
        
        # Connect to mock broker
        await self.broker.connect()
        
        self.is_running = True
        
        # Print initial status
        self._print_status()
        
        logger.info("")
        logger.info("Paper trading is now active.")
        logger.info("The bot will track all trades and validate performance.")
        logger.info("Press Ctrl+C to stop and generate report.")
        logger.info("")
    
    async def stop(self):
        """Stop paper trading"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STOPPING PAPER TRADING SESSION")
        logger.info("=" * 60)
        
        self.is_running = False
        
        # Disconnect broker
        await self.broker.disconnect()
        
        # Save state
        self.validator.save_state()
        
        # Generate final report
        report = self.validator.generate_report()
        print(report)
        
        # Check live trading readiness
        self._check_live_readiness()
    
    async def record_trade(
        self,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        exit_reason: str = ""
    ):
        """Record a completed trade"""
        self.trade_count += 1
        trade_id = f"PAPER_{self.trade_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Record entry
        self.validator.record_trade_entry(
            trade_id=trade_id,
            symbol=self.symbol,
            direction=direction,
            entry_price=entry_price,
            quantity=quantity,
            commission=quantity * 0.0001  # Simulated commission
        )
        
        # Record exit
        self.validator.record_trade_exit(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_reason=exit_reason,
            slippage=abs(entry_price - exit_price) * 0.0001  # Simulated slippage
        )
        
        # Also execute on mock broker for position tracking
        side = OrderSide.BUY if direction == 'buy' else OrderSide.SELL
        await self.broker.place_order(
            symbol=self.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=entry_price
        )
        
        # Close position
        close_side = OrderSide.SELL if direction == 'buy' else OrderSide.BUY
        await self.broker.place_order(
            symbol=self.symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=exit_price
        )
    
    def _print_status(self):
        """Print current status"""
        metrics = self.validator.calculate_metrics()
        result = self.validator.validate()
        
        print("")
        print("=" * 60)
        print("PAPER TRADING STATUS")
        print("=" * 60)
        print(f"Session Start: {self.validator.session_start.strftime('%Y-%m-%d %H:%M')}")
        print(f"Duration: {(datetime.now() - self.validator.session_start).days} days")
        print("")
        print(f"Capital: ${self.validator.current_capital:,.2f} (Started: ${self.validator.initial_capital:,.2f})")
        print(f"Net P&L: ${metrics.net_profit:,.2f} ({metrics.net_profit/self.validator.initial_capital:.1%})")
        print("")
        print(f"Total Trades: {metrics.total_trades}")
        print(f"Win Rate: {metrics.win_rate:.1%}")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        print(f"Max Drawdown: {metrics.max_drawdown_pct:.1%}")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print("")
        print(f"Validation Status: {result.status.value.upper()}")
        print(f"Ready for Live: {'YES' if result.ready_for_live else 'NO'}")
        print("=" * 60)
    
    def _check_live_readiness(self):
        """Check and display live trading readiness"""
        is_ready, passed, failed = self.gate.check_readiness()
        stage = self.gate.get_capital_stage()
        
        print("")
        print("=" * 60)
        print("LIVE TRADING READINESS CHECK")
        print("=" * 60)
        
        print("\nPassed Checks:")
        for check in passed:
            print(f"  [PASS] {check}")
        
        if failed:
            print("\nFailed Checks:")
            for check in failed:
                print(f"  [FAIL] {check}")
        
        print(f"\nRecommended Capital Stage: {stage['name']}")
        print(f"  Capital: ${stage['capital']:,.2f}")
        print(f"  Qualified: {'YES' if stage.get('qualified', False) else 'NO'}")
        
        if is_ready:
            print("\n" + "=" * 60)
            print("[PASS] READY FOR LIVE TRADING")
            print("=" * 60)
            print("\nNext Steps:")
            print("1. Review the validation report carefully")
            print("2. Configure live_trading_config.yaml")
            print("3. Set up broker credentials in .env")
            print("4. Run: python run_live_trading.py --stage 1")
            print("5. Start with Stage 1 capital ($100)")
        else:
            print("\n" + "=" * 60)
            print("[FAIL] NOT READY FOR LIVE TRADING")
            print("=" * 60)
            print("\nContinue paper trading to meet all requirements.")
        
        print("")


async def run_demo_trades(runner: PaperTradingRunner, num_trades: int = 10):
    """Run demo trades for testing"""
    import random
    
    logger.info(f"Running {num_trades} demo trades...")
    
    for i in range(num_trades):
        # Simulate a trade
        direction = random.choice(['buy', 'sell'])
        entry_price = 1.1000 + random.uniform(-0.01, 0.01)
        
        # 55% win rate simulation
        if random.random() < 0.55:
            # Winning trade
            if direction == 'buy':
                exit_price = entry_price + random.uniform(0.001, 0.003)
            else:
                exit_price = entry_price - random.uniform(0.001, 0.003)
            exit_reason = "take_profit"
        else:
            # Losing trade
            if direction == 'buy':
                exit_price = entry_price - random.uniform(0.0005, 0.002)
            else:
                exit_price = entry_price + random.uniform(0.0005, 0.002)
            exit_reason = "stop_loss"
        
        quantity = 10000  # 0.1 lot
        
        await runner.record_trade(
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            exit_reason=exit_reason
        )
        
        logger.info(f"Trade {i+1}/{num_trades} completed")
        await asyncio.sleep(0.1)
    
    logger.info("Demo trades completed")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Paper Trading Runner - Validate before going live"
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD",
        help="Trading symbol (default: EURUSD)"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial capital (default: 10000)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing paper trading data"
    )
    parser.add_argument(
        "--demo",
        type=int,
        default=0,
        help="Run N demo trades for testing"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate report from existing data"
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = PaperTradingRunner(
        symbol=args.symbol,
        initial_capital=args.capital
    )
    
    # Handle validate-only mode
    if args.validate_only or args.report:
        runner.validator.load_state()
        report = runner.validator.generate_report()
        print(report)
        runner._check_live_readiness()
        return
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received...")
        asyncio.create_task(runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start paper trading
    await runner.start()
    
    # Run demo trades if requested
    if args.demo > 0:
        await run_demo_trades(runner, args.demo)
        await runner.stop()
        return
    
    # Keep running until stopped
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
    print("ALPHAALGO PAPER TRADING SYSTEM")
    print("=" * 60)
    print("")
    print("This system validates your trading strategy before going live.")
    print("All trades are simulated with realistic conditions.")
    print("")
    
    asyncio.run(main())
