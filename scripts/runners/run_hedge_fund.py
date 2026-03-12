#!/usr/bin/env python3
"""
AlphaAlgo Hedge Fund AI - Main Runner
=====================================
Institutional-grade hedge fund management system.

Usage:
    python run_hedge_fund.py [--mode MODE] [--capital CAPITAL] [--config CONFIG]

Options:
    --mode      Trading mode: paper, live (default: paper)
    --capital   Initial capital in USD (default: 100000000)
    --config    Path to config file (optional)
"""

import asyncio
import argparse
import logging
import sys
import signal
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'hedge_fund_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Import hedge fund system
try:
    from trading_bot.hedge_fund import (
        HedgeFundOrchestrator,
        create_hedge_fund,
        quick_start,
        FundConfig
    )
    HEDGE_FUND_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import hedge fund system: {e}")
    HEDGE_FUND_AVAILABLE = False


class HedgeFundRunner:
    """Main runner for the hedge fund system"""
    
    def __init__(self, config: dict):
        self.config = config
        self.fund = None
        self._running = False
    
    async def start(self):
        """Start the hedge fund"""
        logger.info("=" * 60)
        logger.info("ALPHAALGO HEDGE FUND AI")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.config.get('mode', 'paper')}")
        logger.info(f"Initial Capital: ${self.config.get('initial_capital', 100_000_000):,.2f}")
        logger.info("=" * 60)
        
        # Create and start fund
        self.fund = create_hedge_fund(self.config)
        await self.fund.start()
        
        self._running = True
        
        # Main loop
        while self._running:
            try:
                # Display status every 30 seconds
                status = self.fund.get_status()
                logger.info(f"Fund Status: {status['state']} | AUM: ${status['aum']:,.2f} | Positions: {status['positions_count']}")
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
    
    async def stop(self):
        """Stop the hedge fund"""
        logger.info("Shutting down hedge fund...")
        self._running = False
        
        if self.fund:
            await self.fund.stop()
        
        logger.info("Hedge fund stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self._running = False


async def interactive_mode(fund: HedgeFundOrchestrator):
    """Interactive command mode"""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    print("Commands:")
    print("  status    - Show fund status")
    print("  metrics   - Show fund metrics")
    print("  investors - List investors")
    print("  add       - Add investor")
    print("  signals   - Generate signals")
    print("  risk      - Show risk status")
    print("  compliance - Show compliance status")
    print("  pb        - Prime broker summary")
    print("  quit      - Exit")
    print("=" * 60)
    
    while True:
        try:
            cmd = input("\nhedge_fund> ").strip().lower()
            
            if cmd == 'quit' or cmd == 'exit':
                break
            
            elif cmd == 'status':
                status = fund.get_status()
                print("\n--- Fund Status ---")
                for key, value in status.items():
                    print(f"  {key}: {value}")
            
            elif cmd == 'metrics':
                metrics = fund.get_fund_metrics()
                print("\n--- Fund Metrics ---")
                print(f"  AUM: ${metrics['fund']['total_aum']:,.2f}")
                print(f"  NAV/Share: ${metrics['fund']['nav_per_share']:,.4f}")
                print(f"  Investors: {metrics['fund']['num_investors']}")
                print(f"  Strategies: {metrics['strategies']['total_strategies']}")
                if metrics['performance']:
                    print(f"  Sharpe Ratio: {metrics['performance']['sharpe_ratio']}")
            
            elif cmd == 'investors':
                summary = fund.fund_manager.get_fund_summary()
                print("\n--- Investors ---")
                print(f"  Total: {summary['investors']['total']}")
                print(f"  By Class: {summary['investors']['by_class']}")
                print(f"  By Type: {summary['investors']['by_type']}")
            
            elif cmd == 'add':
                name = input("  Investor name: ")
                amount = float(input("  Investment amount: "))
                result = fund.add_investor(
                    name=name,
                    investor_type="INSTITUTIONAL",
                    share_class="CLASS_B",
                    investment_amount=amount
                )
                print(f"  Result: {result}")
            
            elif cmd == 'signals':
                # Demo market data
                market_data = {
                    'prices': {
                        'AAPL': {'price': 150, 'returns_20d': 0.05, 'returns_60d': 0.10, 'rsi': 55},
                        'GOOGL': {'price': 140, 'returns_20d': 0.03, 'returns_60d': 0.08, 'rsi': 60},
                        'MSFT': {'price': 380, 'returns_20d': -0.02, 'returns_60d': 0.05, 'rsi': 45}
                    }
                }
                signals = fund.generate_signals(market_data)
                print("\n--- Signals ---")
                print(f"  Total: {signals['total_signals']}")
                print(f"  High Conviction: {signals['high_conviction']}")
            
            elif cmd == 'risk':
                risk = fund.risk_manager.get_risk_summary()
                print("\n--- Risk Status ---")
                for key, value in risk.items():
                    print(f"  {key}: {value}")
            
            elif cmd == 'compliance':
                compliance = fund.get_compliance_status()
                print("\n--- Compliance Status ---")
                for key, value in compliance.items():
                    print(f"  {key}: {value}")
            
            elif cmd == 'pb':
                pb = fund.get_prime_broker_summary()
                print("\n--- Prime Broker Summary ---")
                print(f"  Net Liquidation: ${pb['net_liquidation_value']:,.2f}")
                print(f"  Buying Power: ${pb['buying_power']['standard_buying_power']:,.2f}")
                print(f"  Credit Available: ${pb['credit_available']:,.2f}")
            
            else:
                print(f"  Unknown command: {cmd}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  Error: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AlphaAlgo Hedge Fund AI')
    parser.add_argument('--mode', default='paper', choices=['paper', 'live'],
                        help='Trading mode')
    parser.add_argument('--capital', type=float, default=100_000_000,
                        help='Initial capital in USD')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to config file')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('--demo', action='store_true',
                        help='Run demo')
    
    args = parser.parse_args()
    
    if not HEDGE_FUND_AVAILABLE:
        print("ERROR: Hedge fund system not available")
        sys.exit(1)
    
    # Build config
    config = {
        'fund_name': 'AlphaAlgo Quantitative Fund',
        'mode': args.mode,
        'initial_capital': args.capital
    }
    
    if args.demo:
        # Run demo
        from trading_bot.hedge_fund.hedge_fund_orchestrator import demo
        await demo()
        return
    
    if args.interactive:
        # Interactive mode
        fund = create_hedge_fund(config)
        
        # Add some demo investors
        fund.add_investor(
            name="Seed Investor",
            investor_type="SEED",
            share_class="SEED",
            investment_amount=10_000_000
        )
        
        await interactive_mode(fund)
        return
    
    # Normal operation
    runner = HedgeFundRunner(config)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, runner.handle_signal)
    signal.signal(signal.SIGTERM, runner.handle_signal)
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.stop()


if __name__ == "__main__":
    asyncio.run(main())
