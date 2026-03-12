"""
AlphaAlgo Learning Trading Bot - Self-improving bot with adaptive strategy
"""

import asyncio
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add learning module to path
sys.path.insert(0, os.path.dirname(__file__))
from learning.strategy_optimizer import StrategyOptimizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/learning_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class MarketData:
    symbol: str
    price: float
    rsi: float
    macd: float
    sma_20: float
    sma_50: float
    volatility: float
    timestamp: datetime


@dataclass
class Trade:
    id: int
    symbol: str
    type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    entry_time: datetime
    entry_rsi: float = 0.0
    entry_macd: float = 0.0
    entry_sma_20: float = 0.0
    entry_sma_50: float = 0.0
    entry_volatility: float = 0.0
    entry_hour: int = 0
    exit_time: datetime = None
    exit_price: float = None
    pnl: float = 0.0
    status: TradeStatus = TradeStatus.OPEN
    exit_reason: str = ""


class LearningTradingBot:
    """Self-improving trading bot with adaptive strategy."""
    
    def __init__(self):
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
        
        self.optimizer = StrategyOptimizer(optimization_interval=10)
        self.optimizer.load_knowledge()
        
        self.data_cache = {}
        self.last_update = {}
        
        logger.info("=" * 80)
        logger.info("🧠 AlphaAlgo Learning Trading Bot - INITIALIZED")
        logger.info("=" * 80)
        logger.info(f"RSI Buy Threshold: {self.optimizer.parameters.rsi_buy_threshold:.1f}")
        logger.info(f"RSI Sell Threshold: {self.optimizer.parameters.rsi_sell_threshold:.1f}")
        logger.info(f"Stop Loss: {self.optimizer.parameters.stop_loss_pct:.3%}")
        logger.info(f"Take Profit: {self.optimizer.parameters.take_profit_pct:.3%}")
        logger.info("=" * 80)
    
    def fetch_data(self, ticker: str, symbol_name: str) -> Optional[MarketData]:
        """Fetch real market data."""
        try:
            now = datetime.now()
            if ticker in self.last_update:
                if (now - self.last_update[ticker]).seconds < 60 and ticker in self.data_cache:
                    return self._calc_indicators(self.data_cache[ticker], symbol_name)
            
            logger.info(f"📡 Fetching {symbol_name}...")
            data = yf.download(ticker, period='1d', interval='1m', progress=False)
            
            if data.empty:
                return None
            
            self.data_cache[ticker] = data
            self.last_update[ticker] = now
            return self._calc_indicators(data, symbol_name)
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def _calc_indicators(self, data: pd.DataFrame, symbol: str) -> MarketData:
        """Calculate indicators."""
        price = float(data['Close'].iloc[-1])
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1]) if len(rs) > 0 else 50.0
        
        ema12 = data['Close'].ewm(span=12).mean()
        ema26 = data['Close'].ewm(span=26).mean()
        macd = float((ema12 - ema26).iloc[-1])
        
        sma20 = float(data['Close'].rolling(20).mean().iloc[-1])
        sma50 = float(data['Close'].rolling(50).mean().iloc[-1])
        volatility = float(data['Close'].pct_change().std() * 100)
        
        return MarketData(
            symbol=symbol,
            price=price,
            rsi=rsi,
            macd=macd,
            sma_20=sma20,
            sma_50=sma50,
            volatility=volatility,
            timestamp=datetime.now()
        )
    
    def analyze_market(self, data: MarketData) -> SignalType:
        """Analyze with LEARNED parameters."""
        params = self.optimizer.get_parameters()
        
        logger.info(f"\n📊 {data.symbol} | RSI:{data.rsi:.1f} MACD:{data.macd:.5f}")
        logger.info(f"   Thresholds: Buy<{params.rsi_buy_threshold:.1f} Sell>{params.rsi_sell_threshold:.1f}")
        
        if data.rsi < params.rsi_buy_threshold and data.sma_20 > data.sma_50 and data.macd > 0:
            logger.info(f"   🟢 BUY Signal")
            return SignalType.BUY
        elif data.rsi > params.rsi_sell_threshold and data.sma_20 < data.sma_50 and data.macd < 0:
            logger.info(f"   🔴 SELL Signal")
            return SignalType.SELL
        else:
            logger.info(f"   ⚪ HOLD")
            return SignalType.HOLD
    
    def execute_trade(self, symbol: str, signal: SignalType, data: MarketData) -> Optional[Trade]:
        """Execute with learned parameters."""
        if signal == SignalType.HOLD:
            return None
        
        self.trade_counter += 1
        params = self.optimizer.get_parameters()
        
        if signal == SignalType.BUY:
            sl = data.price * (1 - params.stop_loss_pct)
            tp = data.price * (1 + params.take_profit_pct)
        else:
            sl = data.price * (1 + params.stop_loss_pct)
            tp = data.price * (1 - params.take_profit_pct)
        
        trade = Trade(
            id=self.trade_counter,
            symbol=symbol,
            type=signal.value,
            entry_price=data.price,
            stop_loss=sl,
            take_profit=tp,
            volume=0.1,
            entry_time=datetime.now(),
            entry_rsi=data.rsi,
            entry_macd=data.macd,
            entry_sma_20=data.sma_20,
            entry_sma_50=data.sma_50,
            entry_volatility=data.volatility,
            entry_hour=datetime.now().hour
        )
        
        self.trades.append(trade)
        logger.info(f"\n✅ TRADE #{trade.id} {trade.type} {trade.symbol} @ {trade.entry_price:.5f}")
        logger.info(f"   SL:{sl:.5f} TP:{tp:.5f}")
        return trade
    
    def monitor_positions(self):
        """Monitor open trades."""
        open_trades = [t for t in self.trades if t.status == TradeStatus.OPEN]
        if not open_trades:
            return
        
        logger.info(f"\n👁️ Monitoring {len(open_trades)} position(s)")
        
        for trade in open_trades:
            ticker = next((t for t, n in self.symbols.items() if n == trade.symbol), None)
            if not ticker:
                continue
            
            data = self.fetch_data(ticker, trade.symbol)
            if not data:
                continue
            
            should_close = False
            reason = ""
            
            if trade.type == "BUY":
                if data.price >= trade.take_profit:
                    should_close, reason = True, "TP"
                elif data.price <= trade.stop_loss:
                    should_close, reason = True, "SL"
            else:
                if data.price <= trade.take_profit:
                    should_close, reason = True, "TP"
                elif data.price >= trade.stop_loss:
                    should_close, reason = True, "SL"
            
            if should_close:
                self.close_trade(trade, data.price, reason)
            else:
                pnl = (data.price - trade.entry_price) * 100000 * 0.1
                if trade.type == "SELL":
                    pnl = -pnl
                logger.info(f"   #{trade.id} {trade.symbol}: ${pnl:.2f}")
    
    def close_trade(self, trade: Trade, exit_price: float, reason: str):
        """Close and LEARN."""
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.status = TradeStatus.CLOSED
        trade.exit_reason = reason
        
        if trade.type == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * 100000 * 0.1
        else:
            trade.pnl = (trade.entry_price - exit_price) * 100000 * 0.1
        
        self.total_pnl += trade.pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
            icon = "✅"
        else:
            self.losing_trades += 1
            icon = "❌"
        
        logger.info(f"\n{icon} CLOSED #{trade.id} {reason} | P/L: ${trade.pnl:.2f}")
        
        # LEARN FROM TRADE - Record ALL indicators
        trade_data = {
            'rsi': trade.entry_rsi,
            'macd': trade.entry_macd,
            'sma_20': getattr(trade, 'entry_sma_20', 0),
            'sma_50': getattr(trade, 'entry_sma_50', 0),
            'volatility': getattr(trade, 'entry_volatility', 0),
            'hour': trade.entry_hour,
            'outcome': 'win' if trade.pnl > 0 else 'loss',
            'pnl': trade.pnl,
            'symbol': trade.symbol,
            'type': trade.type
        }
        
        self.optimizer.record_trade(trade_data)
        
        if self.optimizer.should_optimize():
            self.optimizer.optimize()
            self.optimizer.save_knowledge()
    
    def display_stats(self):
        """Display statistics."""
        closed = len([t for t in self.trades if t.status == TradeStatus.CLOSED])
        win_rate = (self.winning_trades / closed * 100) if closed > 0 else 0
        params = self.optimizer.get_parameters()
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 STATISTICS")
        logger.info(f"Trades: {len(self.trades)} | Open: {len([t for t in self.trades if t.status == TradeStatus.OPEN])}")
        logger.info(f"Wins: {self.winning_trades} | Losses: {self.losing_trades} | Rate: {win_rate:.1f}%")
        logger.info(f"Total P/L: ${self.total_pnl:.2f}")
        logger.info("🧠 LEARNED PARAMETERS")
        logger.info(f"RSI: {params.rsi_buy_threshold:.1f}/{params.rsi_sell_threshold:.1f} | SL: {params.stop_loss_pct:.3%} | Updates: {params.update_count}")
        logger.info("=" * 80)
    
    async def run(self):
        """Main loop."""
        logger.info("\n🚀 Starting learning bot...")
        cycle = 0
        
        try:
            while True:
                cycle += 1
                logger.info(f"\n{'='*80}\n⏰ Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}\n{'='*80}")
                
                import random
                ticker, symbol = random.choice(list(self.symbols.items()))
                
                data = self.fetch_data(ticker, symbol)
                if data:
                    signal = self.analyze_market(data)
                    
                    open_count = len([t for t in self.trades if t.status == TradeStatus.OPEN])
                    if signal != SignalType.HOLD and open_count < 3:
                        self.execute_trade(symbol, signal, data)
                    
                    self.monitor_positions()
                    
                    if cycle % 5 == 0:
                        self.display_stats()
                
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Stopping...")
            
            for trade in [t for t in self.trades if t.status == TradeStatus.OPEN]:
                ticker = next((t for t, n in self.symbols.items() if n == trade.symbol), None)
                if ticker:
                    data = self.fetch_data(ticker, trade.symbol)
                    if data:
                        self.close_trade(trade, data.price, "Manual")
            
            self.display_stats()
            self.optimizer.save_knowledge()
            logger.info("\n✅ Learning bot stopped")


async def main():
    bot = LearningTradingBot()
    await bot.run()


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    os.makedirs('knowledge', exist_ok=True)
    asyncio.run(main())
