"""
AlphaAlgo Real Data Trading Bot
Uses REAL market data from Yahoo Finance instead of simulated prices
"""

import asyncio
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/real_data_trading.log'),
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
    type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    entry_time: datetime
    exit_time: datetime = None
    exit_price: float = None
    pnl: float = 0.0
    status: TradeStatus = TradeStatus.OPEN


class RealDataTradingBot:
    """
    Real data trading bot using Yahoo Finance.
    
    Features:
    1. Fetches REAL market data
    2. Calculates REAL technical indicators
    3. Generates trading signals
    4. Executes trades (simulated execution, real prices)
    5. Monitors positions with real price updates
    6. Tracks P/L based on real market movements
    """
    
    def __init__(self):
        """Initialize real data bot."""
        # Forex symbols (Yahoo Finance format)
        self.symbols = {
            'EURUSD=X': 'EURUSD',
            'GBPUSD=X': 'GBPUSD',
            'USDJPY=X': 'USDJPY',
            'AUDUSD=X': 'AUDUSD',
            'USDCAD=X': 'USDCAD'
        }
        
        self.trades: List[Trade] = []
        self.trade_counter = 0
        self.total_pnl = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Cache for historical data
        self.data_cache = {}
        self.last_update = {}
        
        logger.info("=" * 80)
        logger.info("🎯 AlphaAlgo Real Data Trading Bot")
        logger.info("=" * 80)
        logger.info("Using REAL market data from Yahoo Finance")
        logger.info("Symbols: " + ", ".join(self.symbols.values()))
        logger.info("=" * 80)
    
    def fetch_real_market_data(self, ticker: str, symbol_name: str) -> Optional[MarketData]:
        """
        Fetch REAL market data from Yahoo Finance.
        
        This replaces the simulated generate_market_data() function!
        """
        try:
            # Check if we need to update cache (every 60 seconds)
            now = datetime.now()
            if ticker in self.last_update:
                time_diff = (now - self.last_update[ticker]).seconds
                if time_diff < 60 and ticker in self.data_cache:
                    # Use cached data if less than 60 seconds old
                    return self._calculate_indicators(self.data_cache[ticker], symbol_name)
            
            # Fetch fresh data
            logger.info(f"📡 Fetching real data for {symbol_name}...")
            
            # Get 1 day of 1-minute data for technical indicators
            data = yf.download(ticker, period='1d', interval='1m', progress=False)
            
            if data.empty:
                logger.warning(f"⚠️ No data available for {symbol_name}")
                return None
            
            # Cache the data
            self.data_cache[ticker] = data
            self.last_update[ticker] = now
            
            return self._calculate_indicators(data, symbol_name)
        
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol_name}: {e}")
            return None
    
    def _calculate_indicators(self, data: pd.DataFrame, symbol_name: str) -> MarketData:
        """Calculate technical indicators from real data."""
        
        # Get current price (last close)
        current_price = float(data['Close'].iloc[-1])
        
        # Calculate volume
        volume = int(data['Volume'].iloc[-1]) if 'Volume' in data.columns else 0
        
        # Simulate bid/ask spread (0.0001 or 1 pip)
        spread = current_price * 0.0001
        bid = current_price - spread / 2
        ask = current_price + spread / 2
        
        # Calculate RSI (14 periods)
        rsi = self._calculate_rsi(data['Close'], 14)
        
        # Calculate MACD
        macd = self._calculate_macd(data['Close'])
        
        # Calculate SMAs
        sma_20 = float(data['Close'].rolling(20).mean().iloc[-1])
        sma_50 = float(data['Close'].rolling(50).mean().iloc[-1])
        
        return MarketData(
            symbol=symbol_name,
            price=current_price,
            bid=bid,
            ask=ask,
            volume=volume,
            timestamp=datetime.now(),
            rsi=rsi,
            macd=macd,
            sma_20=sma_20,
            sma_50=sma_50
        )
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1])
        except:
            return 50.0  # Neutral if calculation fails
    
    def _calculate_macd(self, prices: pd.Series) -> float:
        """Calculate MACD indicator."""
        try:
            ema_12 = prices.ewm(span=12, adjust=False).mean()
            ema_26 = prices.ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            
            return float(macd.iloc[-1])
        except:
            return 0.0
    
    def analyze_market(self, data: MarketData) -> SignalType:
        """Analyze market data and generate trading signal."""
        logger.info(f"\n📊 ANALYZING: {data.symbol} (REAL DATA)")
        logger.info(f"   Price: {data.price:.5f} (REAL)")
        logger.info(f"   RSI: {data.rsi:.2f}")
        logger.info(f"   MACD: {data.macd:.5f}")
        logger.info(f"   SMA(20): {data.sma_20:.5f}")
        logger.info(f"   SMA(50): {data.sma_50:.5f}")
        
        # Trading strategy: RSI + Moving Average Crossover
        signal = SignalType.HOLD
        
        # Oversold + Bullish = BUY
        if data.rsi < 40 and data.sma_20 > data.sma_50 and data.macd > 0:
            signal = SignalType.BUY
            logger.info(f"   🟢 Signal: BUY (RSI oversold + bullish trend)")
        
        # Overbought + Bearish = SELL
        elif data.rsi > 60 and data.sma_20 < data.sma_50 and data.macd < 0:
            signal = SignalType.SELL
            logger.info(f"   🔴 Signal: SELL (RSI overbought + bearish trend)")
        
        else:
            logger.info(f"   ⚪ Signal: HOLD (no clear setup)")
        
        return signal
    
    def execute_trade(self, symbol: str, signal: SignalType, price: float) -> Optional[Trade]:
        """Execute a trade based on signal."""
        if signal == SignalType.HOLD:
            return None
        
        self.trade_counter += 1
        volume = 0.1  # Standard lot
        
        if signal == SignalType.BUY:
            stop_loss = price * 0.995  # 0.5% stop
            take_profit = price * 1.015  # 1.5% target
        else:  # SELL
            stop_loss = price * 1.005
            take_profit = price * 0.985
        
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
        
        logger.info(f"\n✅ TRADE EXECUTED #{trade.id} (REAL PRICE)")
        logger.info(f"   Symbol: {trade.symbol}")
        logger.info(f"   Type: {trade.type}")
        logger.info(f"   Entry: {trade.entry_price:.5f} (REAL)")
        logger.info(f"   Stop Loss: {trade.stop_loss:.5f}")
        logger.info(f"   Take Profit: {trade.take_profit:.5f}")
        logger.info(f"   Volume: {trade.volume}")
        
        return trade
    
    def monitor_positions(self):
        """Monitor open positions with REAL price updates."""
        open_trades = [t for t in self.trades if t.status == TradeStatus.OPEN]
        
        if not open_trades:
            return
        
        logger.info(f"\n👁️ MONITORING {len(open_trades)} OPEN POSITION(S) (REAL PRICES)")
        
        for trade in open_trades:
            # Get REAL current price
            ticker = None
            for t, name in self.symbols.items():
                if name == trade.symbol:
                    ticker = t
                    break
            
            if not ticker:
                continue
            
            data = self.fetch_real_market_data(ticker, trade.symbol)
            if not data:
                continue
            
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
                # Calculate floating P/L (realistic calculation)
                if trade.type == "BUY":
                    pnl = (current_price - trade.entry_price) * trade.volume * 100000
                else:
                    pnl = (trade.entry_price - current_price) * trade.volume * 100000
                
                logger.info(f"   Trade #{trade.id}: {trade.symbol} {trade.type}")
                logger.info(f"   Entry: {trade.entry_price:.5f} | Current: {current_price:.5f} (REAL)")
                logger.info(f"   Floating P/L: ${pnl:.2f}")
    
    def close_trade(self, trade: Trade, exit_price: float, reason: str):
        """Close a trade and calculate P/L."""
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.status = TradeStatus.CLOSED
        
        # Calculate realistic P/L
        if trade.type == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * trade.volume * 100000
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.volume * 100000
        
        self.total_pnl += trade.pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
            result_icon = "✅"
        else:
            self.losing_trades += 1
            result_icon = "❌"
        
        logger.info(f"\n{result_icon} TRADE CLOSED #{trade.id} - {reason} (REAL PRICE)")
        logger.info(f"   Symbol: {trade.symbol}")
        logger.info(f"   Type: {trade.type}")
        logger.info(f"   Entry: {trade.entry_price:.5f}")
        logger.info(f"   Exit: {trade.exit_price:.5f} (REAL)")
        logger.info(f"   P/L: ${trade.pnl:.2f}")
        logger.info(f"   Duration: {(trade.exit_time - trade.entry_time).seconds}s")
    
    def display_statistics(self):
        """Display trading statistics."""
        total_trades = len(self.trades)
        open_trades = len([t for t in self.trades if t.status == TradeStatus.OPEN])
        closed_trades = len([t for t in self.trades if t.status == TradeStatus.CLOSED])
        
        win_rate = (self.winning_trades / closed_trades * 100) if closed_trades > 0 else 0
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 TRADING STATISTICS (REAL DATA)")
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
        """Main trading loop with REAL data."""
        logger.info("\n🚀 Starting REAL data trading bot...")
        logger.info("📡 Fetching data from Yahoo Finance")
        logger.info("Press Ctrl+C to stop\n")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                logger.info(f"\n{'=' * 80}")
                logger.info(f"📈 TRADING CYCLE #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'=' * 80}")
                
                # Randomly select a symbol to analyze
                import random
                ticker, symbol_name = random.choice(list(self.symbols.items()))
                
                # 1. Fetch REAL market data
                data = self.fetch_real_market_data(ticker, symbol_name)
                
                if data:
                    # 2. Analyze and generate signal
                    signal = self.analyze_market(data)
                    
                    # 3. Execute trade if signal and not too many open
                    if signal != SignalType.HOLD and len([t for t in self.trades if t.status == TradeStatus.OPEN]) < 3:
                        self.execute_trade(symbol_name, signal, data.price)
                    
                    # 4. Monitor open positions with REAL prices
                    self.monitor_positions()
                    
                    # 5. Display statistics every 5 cycles
                    if cycle % 5 == 0:
                        self.display_statistics()
                
                # Wait before next cycle (60 seconds for real data)
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Bot stopped by user")
            
            # Close all open positions
            open_trades = [t for t in self.trades if t.status == TradeStatus.OPEN]
            for trade in open_trades:
                ticker = None
                for t, name in self.symbols.items():
                    if name == trade.symbol:
                        ticker = t
                        break
                if ticker:
                    data = self.fetch_real_market_data(ticker, trade.symbol)
                    if data:
                        self.close_trade(trade, data.price, "Manual Close")
            
            # Final statistics
            self.display_statistics()
            
            logger.info("\n✅ Real data trading bot stopped")


async def main():
    """Main entry point."""
    bot = RealDataTradingBot()
    await bot.run()


if __name__ == '__main__':
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Run bot
    asyncio.run(main())
