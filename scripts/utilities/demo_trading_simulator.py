"""
AlphaAlgo Demo Trading Simulator
Simulates complete trading activity: analysis, signals, execution, monitoring
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/demo_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeStatus(Enum):
    """Trade status."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: int
    timestamp: datetime
    
    # Technical indicators
    rsi: float
    macd: float
    sma_20: float
    sma_50: float


@dataclass
class Trade:
    """Trade structure."""
    id: int
    symbol: str
    type: str  # BUY or SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    entry_time: datetime
    exit_time: datetime = None
    exit_price: float = None
    pnl: float = 0.0
    status: TradeStatus = TradeStatus.OPEN


class DemoTradingSimulator:
    """
    Demo trading simulator that shows complete trading workflow:
    1. Market data analysis
    2. Signal generation
    3. Trade execution
    4. Position monitoring
    5. P/L tracking
    """
    
    def __init__(self):
        """Initialize demo simulator."""
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
        self.trades: List[Trade] = []
        self.trade_counter = 0
        self.total_pnl = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Starting prices for each symbol
        self.prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'AUDUSD': 0.6450,
            'USDCAD': 1.3650
        }
        
        logger.info("=" * 80)
        logger.info("🎯 AlphaAlgo Demo Trading Simulator")
        logger.info("=" * 80)
        logger.info("This simulator demonstrates complete trading workflow:")
        logger.info("  1. Market Data Analysis")
        logger.info("  2. Technical Indicator Calculation")
        logger.info("  3. Signal Generation")
        logger.info("  4. Trade Execution")
        logger.info("  5. Position Monitoring")
        logger.info("  6. P/L Tracking")
        logger.info("=" * 80)
    
    def generate_market_data(self, symbol: str) -> MarketData:
        """Generate simulated market data."""
        # Simulate price movement
        current_price = self.prices[symbol]
        change = random.uniform(-0.002, 0.002)  # ±0.2% movement
        new_price = current_price * (1 + change)
        self.prices[symbol] = new_price
        
        spread = new_price * 0.0001  # 1 pip spread
        
        # Generate technical indicators
        rsi = random.uniform(30, 70)
        macd = random.uniform(-0.001, 0.001)
        sma_20 = new_price * random.uniform(0.998, 1.002)
        sma_50 = new_price * random.uniform(0.995, 1.005)
        
        return MarketData(
            symbol=symbol,
            price=new_price,
            bid=new_price - spread/2,
            ask=new_price + spread/2,
            volume=random.randint(1000, 10000),
            timestamp=datetime.now(),
            rsi=rsi,
            macd=macd,
            sma_20=sma_20,
            sma_50=sma_50
        )
    
    def analyze_market(self, data: MarketData) -> SignalType:
        """Analyze market data and generate trading signal."""
        logger.info(f"\n📊 ANALYZING: {data.symbol}")
        logger.info(f"   Price: {data.price:.5f}")
        logger.info(f"   RSI: {data.rsi:.2f}")
        logger.info(f"   MACD: {data.macd:.5f}")
        logger.info(f"   SMA(20): {data.sma_20:.5f}")
        logger.info(f"   SMA(50): {data.sma_50:.5f}")
        
        # Simple strategy: RSI + Moving Average Crossover
        signal = SignalType.HOLD
        
        # Oversold + Bullish crossover = BUY
        if data.rsi < 40 and data.sma_20 > data.sma_50 and data.macd > 0:
            signal = SignalType.BUY
            logger.info(f"   🟢 Signal: BUY (RSI oversold + bullish trend)")
        
        # Overbought + Bearish crossover = SELL
        elif data.rsi > 60 and data.sma_20 < data.sma_50 and data.macd < 0:
            signal = SignalType.SELL
            logger.info(f"   🔴 Signal: SELL (RSI overbought + bearish trend)")
        
        else:
            logger.info(f"   ⚪ Signal: HOLD (no clear setup)")
        
        return signal
    
    def execute_trade(self, symbol: str, signal: SignalType, price: float) -> Trade:
        """Execute a trade based on signal."""
        if signal == SignalType.HOLD:
            return None
        
        self.trade_counter += 1
        volume = 0.1  # Standard lot size
        
        if signal == SignalType.BUY:
            stop_loss = price * 0.995  # 0.5% stop loss
            take_profit = price * 1.015  # 1.5% take profit
        else:  # SELL
            stop_loss = price * 1.005  # 0.5% stop loss
            take_profit = price * 0.985  # 1.5% take profit
        
        trade = Trade(
            id=self.trade_counter,
            symbol=symbol,
            type=signal.value,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volume=volume,
            entry_time=datetime.now()
        )
        
        self.trades.append(trade)
        
        logger.info(f"\n✅ TRADE EXECUTED #{trade.id}")
        logger.info(f"   Symbol: {trade.symbol}")
        logger.info(f"   Type: {trade.type}")
        logger.info(f"   Entry: {trade.entry_price:.5f}")
        logger.info(f"   Stop Loss: {trade.stop_loss:.5f}")
        logger.info(f"   Take Profit: {trade.take_profit:.5f}")
        logger.info(f"   Volume: {trade.volume}")
        
        return trade
    
    def monitor_positions(self):
        """Monitor open positions and close if TP/SL hit."""
        open_trades = [t for t in self.trades if t.status == TradeStatus.OPEN]
        
        if not open_trades:
            return
        
        logger.info(f"\n👁️ MONITORING {len(open_trades)} OPEN POSITION(S)")
        
        for trade in open_trades:
            # Get current price
            data = self.generate_market_data(trade.symbol)
            current_price = data.price
            
            # Check if TP or SL hit
            should_close = False
            exit_reason = ""
            
            if trade.type == "BUY":
                if current_price >= trade.take_profit:
                    should_close = True
                    exit_reason = "Take Profit"
                elif current_price <= trade.stop_loss:
                    should_close = True
                    exit_reason = "Stop Loss"
            else:  # SELL
                if current_price <= trade.take_profit:
                    should_close = True
                    exit_reason = "Take Profit"
                elif current_price >= trade.stop_loss:
                    should_close = True
                    exit_reason = "Stop Loss"
            
            if should_close:
                self.close_trade(trade, current_price, exit_reason)
            else:
                # Calculate floating P/L
                if trade.type == "BUY":
                    pnl = (current_price - trade.entry_price) * trade.volume * 100000
                else:
                    pnl = (trade.entry_price - current_price) * trade.volume * 100000
                
                logger.info(f"   Trade #{trade.id}: {trade.symbol} {trade.type}")
                logger.info(f"   Entry: {trade.entry_price:.5f} | Current: {current_price:.5f}")
                logger.info(f"   Floating P/L: ${pnl:.2f}")
    
    def close_trade(self, trade: Trade, exit_price: float, reason: str):
        """Close a trade and calculate P/L."""
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.status = TradeStatus.CLOSED
        
        # Calculate P/L
        if trade.type == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * trade.volume * 100000
        else:  # SELL
            trade.pnl = (trade.entry_price - exit_price) * trade.volume * 100000
        
        self.total_pnl += trade.pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
            result_icon = "✅"
        else:
            self.losing_trades += 1
            result_icon = "❌"
        
        logger.info(f"\n{result_icon} TRADE CLOSED #{trade.id} - {reason}")
        logger.info(f"   Symbol: {trade.symbol}")
        logger.info(f"   Type: {trade.type}")
        logger.info(f"   Entry: {trade.entry_price:.5f}")
        logger.info(f"   Exit: {trade.exit_price:.5f}")
        logger.info(f"   P/L: ${trade.pnl:.2f}")
        logger.info(f"   Duration: {(trade.exit_time - trade.entry_time).seconds}s")
    
    def display_statistics(self):
        """Display trading statistics."""
        total_trades = len(self.trades)
        open_trades = len([t for t in self.trades if t.status == TradeStatus.OPEN])
        closed_trades = len([t for t in self.trades if t.status == TradeStatus.CLOSED])
        
        win_rate = (self.winning_trades / closed_trades * 100) if closed_trades > 0 else 0
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 TRADING STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Open Positions: {open_trades}")
        logger.info(f"Closed Trades: {closed_trades}")
        logger.info(f"Winning Trades: {self.winning_trades}")
        logger.info(f"Losing Trades: {self.losing_trades}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Total P/L: ${self.total_pnl:.2f}")
        logger.info("=" * 80)
    
    async def run(self):
        """Main simulation loop."""
        logger.info("\n🚀 Starting demo trading simulation...")
        logger.info("Press Ctrl+C to stop\n")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                logger.info(f"\n{'=' * 80}")
                logger.info(f"📈 TRADING CYCLE #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'=' * 80}")
                
                # Randomly select a symbol to analyze
                symbol = random.choice(self.symbols)
                
                # 1. Generate market data
                data = self.generate_market_data(symbol)
                
                # 2. Analyze and generate signal
                signal = self.analyze_market(data)
                
                # 3. Execute trade if signal is not HOLD
                if signal != SignalType.HOLD and len([t for t in self.trades if t.status == TradeStatus.OPEN]) < 3:
                    self.execute_trade(symbol, signal, data.price)
                
                # 4. Monitor open positions
                self.monitor_positions()
                
                # 5. Display statistics every 5 cycles
                if cycle % 5 == 0:
                    self.display_statistics()
                
                # Wait before next cycle
                await asyncio.sleep(15)  # Check every 15 seconds
        
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Simulation stopped by user")
            
            # Close all open positions
            open_trades = [t for t in self.trades if t.status == TradeStatus.OPEN]
            for trade in open_trades:
                data = self.generate_market_data(trade.symbol)
                self.close_trade(trade, data.price, "Manual Close")
            
            # Final statistics
            self.display_statistics()
            
            logger.info("\n✅ Demo simulation complete")


async def main():
    """Main entry point."""
    simulator = DemoTradingSimulator()
    await simulator.run()


if __name__ == '__main__':
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Run simulator
    asyncio.run(main())
