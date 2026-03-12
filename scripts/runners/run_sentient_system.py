#!/usr/bin/env python3
"""
Sentient Trading System - Main Runner

An autonomous self-evolving trading bot that:
- Monitors WiFi/internet and auto-activates
- Browses the internet for sentiment and knowledge
- Learns from other AI trading systems
- Protects itself from hackers
- Analyzes and improves its own code
- Evolves continuously to maximize profits

Usage:
    python run_sentient_system.py [--mode paper|live] [--capital 10000]
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.sentient_core import (
    SentientOrchestrator,
    create_sentient_system,
    TradingMode,
    SystemState,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/sentient_{datetime.now().strftime("%Y%m%d")}.log'),
    ]
)
logger = logging.getLogger(__name__)


class SentientRunner:
    """Runner for the Sentient Trading System"""
    
    def __init__(self, config: dict):
        self.config = config
        self.system: SentientOrchestrator = None
        self.is_running = False
    
    async def start(self):
        """Start the sentient system"""
        print("\n" + "="*60)
        print("   SENTIENT TRADING SYSTEM")
        print("   Autonomous Self-Evolving Trading Bot")
        print("="*60 + "\n")
        
        print("Initializing systems...")
        self.system = create_sentient_system(self.config)
        
        # Setup signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                asyncio.get_event_loop().add_signal_handler(
                    sig, lambda: asyncio.create_task(self.shutdown())
                )
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                signal.signal(sig, lambda s, f: asyncio.create_task(self.shutdown()))
        
        self.is_running = True
        
        # Start the system
        await self.system.start()
        
        print("\n" + "-"*60)
        print("System started! Monitoring network connection...")
        print("-"*60 + "\n")
        
        # Main display loop
        await self._display_loop()
    
    async def shutdown(self):
        """Shutdown the system gracefully"""
        if not self.is_running:
            return
        
        print("\n\nShutting down...")
        self.is_running = False
        
        if self.system:
            await self.system.stop()
        
        print("Goodbye!")
    
    async def _display_loop(self):
        """Display system status periodically"""
        while self.is_running:
            try:
                await self._display_status()
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Display error: {e}")
                await asyncio.sleep(5)
    
    async def _display_status(self):
        """Display current system status"""
        if not self.system:
            return
        
        status = self.system.get_status()
        
        # Clear screen (optional)
        # print("\033[2J\033[H", end="")
        
        print("\n" + "="*60)
        print(f"  SENTIENT SYSTEM STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # Connection status
        conn_icon = "🟢" if status.is_connected else "🔴"
        print(f"\n  {conn_icon} Network: {'Connected' if status.is_connected else 'Disconnected'}")
        print(f"  📊 Trading Mode: {status.trading_mode.name}")
        print(f"  🔒 Security: {status.threat_level.name}")
        print(f"  ⚙️  State: {status.state.name}")
        
        # Active systems
        print(f"\n  Active Systems: {', '.join(status.active_systems)}")
        
        # Knowledge stats
        print(f"\n  📚 Knowledge Items: {status.knowledge_items}")
        print(f"  🧠 Techniques Learned: {status.techniques_learned}")
        print(f"  🔍 Flaws Detected: {status.flaws_detected}")
        print(f"  🔄 Changes Applied: {status.changes_applied}")
        
        # Performance
        print(f"\n  💰 Total PnL: ${status.total_pnl:.2f}")
        print(f"  ⏱️  Uptime: {status.uptime_seconds/3600:.1f} hours")
        
        if status.last_evolution:
            print(f"  🧬 Last Evolution: {status.last_evolution.strftime('%Y-%m-%d %H:%M')}")
        
        # Get sentiment
        sentiment = self.system.get_sentiment()
        if sentiment.get('count', 0) > 0:
            sent_icon = "📈" if sentiment['overall'] > 0 else "📉" if sentiment['overall'] < 0 else "➡️"
            print(f"\n  {sent_icon} Market Sentiment: {sentiment['overall']:.2f}")
            print(f"     Bullish: {sentiment.get('bullish_pct', 0):.1f}%")
            print(f"     Bearish: {sentiment.get('bearish_pct', 0):.1f}%")
        
        # Performance metrics
        metrics = self.system.get_performance_metrics()
        if metrics['total_trades'] > 0:
            print(f"\n  📊 Performance Metrics:")
            print(f"     Trades: {metrics['total_trades']}")
            print(f"     Win Rate: {metrics['win_rate']*100:.1f}%")
            print(f"     Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"     Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"     Max Drawdown: {metrics['max_drawdown']*100:.1f}%")
        
        print("\n" + "-"*60)
        print("  Press Ctrl+C to stop")
        print("-"*60)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sentient Trading System - Autonomous Self-Evolving Bot'
    )
    parser.add_argument(
        '--mode',
        choices=['paper', 'live'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=10000.0,
        help='Initial capital (default: 10000)'
    )
    parser.add_argument(
        '--risk',
        type=float,
        default=0.02,
        help='Risk per trade as decimal (default: 0.02 = 2%%)'
    )
    parser.add_argument(
        '--harvest-interval',
        type=int,
        default=300,
        help='Knowledge harvest interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--learning-interval',
        type=int,
        default=3600,
        help='AI learning interval in seconds (default: 3600)'
    )
    parser.add_argument(
        '--analysis-interval',
        type=int,
        default=3600,
        help='Self-analysis interval in seconds (default: 3600)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    args = parse_args()
    
    config = {
        'mode': args.mode,
        'initial_capital': args.capital,
        'risk_per_trade': args.risk,
        'harvest_interval': args.harvest_interval,
        'learning_interval': args.learning_interval,
        'analysis_interval': args.analysis_interval,
    }
    
    print(f"\nConfiguration:")
    print(f"  Mode: {args.mode}")
    print(f"  Capital: ${args.capital:,.2f}")
    print(f"  Risk per trade: {args.risk*100:.1f}%")
    
    runner = SentientRunner(config)
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        await runner.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await runner.shutdown()
        raise


if __name__ == '__main__':
    asyncio.run(main())
