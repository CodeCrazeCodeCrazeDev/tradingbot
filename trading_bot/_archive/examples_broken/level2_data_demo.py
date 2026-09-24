"""
Level 2 (Order Book) Data Demo
Demonstrates Level 2 data integration from multiple sources
"""

import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_signal(signal):
    pass
    """Handle Level 2 trading signal"""
    print(f"\n{'='*60}")
    print(f"LEVEL 2 SIGNAL")
    print(f"{'='*60}")
    print(f"Symbol: {signal.symbol}")
    print(f"Type: {signal.signal_type.upper()}")
    print(f"Strength: {signal.strength:.2%}")
    print(f"Reason: {signal.reason}")
    print(f"Metrics: {signal.metrics}")
    print(f"{'='*60}\n")


async def on_alert(alert):
    pass
    """Handle Level 2 alert"""
    print(f"\n*** ALERT: {alert} ***\n")


async def print_order_book(order_book):
    pass
    """Pretty print order book"""
    print(f"\n{'='*60}")
    print(f"ORDER BOOK: {order_book.symbol} ({order_book.source.value})")
    print(f"{'='*60}")
    print(f"{'BIDS':<30} | {'ASKS':>30}")
    print(f"{'-'*30} | {'-'*30}")
    
    max_levels = min(10, max(len(order_book.bids), len(order_book.asks)))
    
    for i in range(max_levels):
    pass
        bid_str = ""
        ask_str = ""
        
        if i < len(order_book.bids):
    pass
            bid = order_book.bids[i]
            bid_str = f"{bid.size:>12.4f} @ {bid.price:<12.5f}"
        
        if i < len(order_book.asks):
    pass
            ask = order_book.asks[i]
            ask_str = f"{ask.price:>12.5f} @ {ask.size:<12.4f}"
        
        print(f"{bid_str:<30} | {ask_str:>30}")
    
    print(f"{'-'*60}")
    print(f"Spread: {order_book.spread:.5f} ({order_book.spread_percent:.4f}%)")
    print(f"Mid Price: {order_book.mid_price:.5f}")
    print(f"Imbalance: {order_book.imbalance:.2%}")
    print(f"Total Bid Volume: {order_book.total_bid_volume:.4f}")
    print(f"Total Ask Volume: {order_book.total_ask_volume:.4f}")
    print(f"{'='*60}\n")


async def demo_ticktrader():
    pass
    """Demo TickTrader Level 2 data"""
    print("\n" + "="*60)
    print("TICKTRADER / FXOPEN LEVEL 2 DEMO")
    print("="*60)
    
    # Check credentials
    login = os.getenv('TICKTRADER_LOGIN')
    password = os.getenv('TICKTRADER_PASSWORD')
    server = os.getenv('TICKTRADER_SERVER')
    
    if not all([login, password, server]):
    pass
        print("TickTrader credentials not configured in .env")
        print("Required: TICKTRADER_LOGIN, TICKTRADER_PASSWORD, TICKTRADER_SERVER")
        return
    
    print(f"Login: {login}")
    print(f"Server: {server}")
    
    try:
    pass
        from trading_bot.connectors.ticktrader_connector import (
            TickTraderConnector,
            TickTraderConfig
        )
        from trading_bot.data.level2_data_handler import Level2DataHandler
        
        # Create handler
        handler = Level2DataHandler()
        handler.register_handler('signal', on_signal)
        
        # Create connector
        config = TickTraderConfig(
            login=login,
            password=password,
            server=server
        )
        
        connector = TickTraderConnector(config)
        
        # Register order book handler
        async def handle_order_book(order_book):
    pass
            await print_order_book(order_book)
            await handler.process_order_book(order_book)
        
        connector.register_handler('order_book', handle_order_book)
        
        # Connect
        print("\nConnecting to TickTrader...")
        if await connector.connect():
    pass
            print("Connected!")
            
            # Get available symbols
            symbols = await connector.get_symbols()
            if symbols:
    pass
                print(f"\nAvailable symbols: {len(symbols)}")
                for sym in symbols[:10]:
    pass
                    print(f"  - {sym.get('Symbol', sym)}")
            
            # Get account info
            account = await connector.get_account_info()
            if account:
    pass
                print(f"\nAccount: {account}")
            
            # Subscribe to forex pairs
            forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
            print(f"\nSubscribing to Level 2: {forex_symbols}")
            await connector.subscribe_level2(forex_symbols)
            
            # Run for a while to receive data
            print("\nReceiving Level 2 data (30 seconds)...")
            await asyncio.sleep(30)
            
            # Disconnect
            await connector.disconnect()
            print("\nDisconnected from TickTrader")
            
        else:
    pass
            print("Failed to connect to TickTrader")
            
    except Exception as e:
    pass
        logger.error(f"TickTrader demo error: {e}")
        import traceback
        traceback.print_exc()


async def demo_binance():
    pass
    """Demo Binance Level 2 data"""
    print("\n" + "="*60)
    print("BINANCE LEVEL 2 DEMO")
    print("="*60)
    
    api_key = os.getenv('BINANCE_API_KEY')
    
    if not api_key:
    pass
        print("Binance API key not configured in .env")
        return
    
    print(f"API Key: {api_key[:10]}...")
    
    try:
    pass
        from trading_bot.connectors.binance_connector import BinanceConnector
        from trading_bot.data.level2_data_handler import (
            Level2DataHandler, OrderBook, OrderBookLevel, OrderBookSource
        )
        
        # Create handler
        handler = Level2DataHandler()
        handler.register_handler('signal', on_signal)
        
        # Create connector
        connector = BinanceConnector({
            'api_key': api_key,
            'api_secret': os.getenv('BINANCE_API_SECRET', ''),
            'testnet': True
        })
        
        # Register order book handler
        async def handle_order_book(order_book_data):
    pass
            # Convert to our OrderBook format if needed
            if hasattr(order_book_data, 'bids'):
    pass
                order_book = OrderBook(
                    symbol=order_book_data.symbol,
                    source=OrderBookSource.BINANCE,
                    timestamp=order_book_data.timestamp,
                    bids=[OrderBookLevel(price=b[0], size=b[1]) for b in order_book_data.bids],
                    asks=[OrderBookLevel(price=a[0], size=a[1]) for a in order_book_data.asks]
                )
                await print_order_book(order_book)
                await handler.process_order_book(order_book)
        
        connector.event_handlers = {'order_book': [handle_order_book]}
        
        # Connect
        print("\nConnecting to Binance...")
        await connector.connect()
        print("Connected!")
        
        # Subscribe to crypto pairs
        crypto_symbols = ['BTCUSDT', 'ETHUSDT']
        print(f"\nSubscribing to Level 2: {crypto_symbols}")
        await connector.subscribe_order_book(crypto_symbols, depth=10)
        
        # Run for a while
        print("\nReceiving Level 2 data (30 seconds)...")
        await asyncio.sleep(30)
        
        # Disconnect
        await connector.disconnect()
        print("\nDisconnected from Binance")
        
    except Exception as e:
    pass
        logger.error(f"Binance demo error: {e}")
        traceback.print_exc()


async def demo_unified_manager():
    pass
    """Demo unified Level 2 manager"""
    print("\n" + "="*60)
    print("UNIFIED LEVEL 2 MANAGER DEMO")
    print("="*60)
    
    try:
    pass
        from trading_bot.data.level2_manager import start_level2_manager
        
        # Start manager
        print("\nStarting Level 2 Manager...")
        manager = await start_level2_manager()
        
        # Register callbacks
        manager.register_signal_callback(on_signal)
        manager.register_alert_callback(on_alert)
        
        # Print status
        status = manager.get_status()
        print(f"\nManager Status:")
        print(f"  Running: {status['running']}")
        print(f"  Connectors: {status['connectors']}")
        
        # Subscribe based on available connectors
        if 'ticktrader' in status['connectors']:
    pass
            await manager.subscribe_forex(['EURUSD', 'GBPUSD'])
        
        if 'binance' in status['connectors']:
    pass
            await manager.subscribe_crypto(['BTCUSDT', 'ETHUSDT'])
        
        # Run for a while
        print("\nReceiving Level 2 data (60 seconds)...")
        
        for i in range(12):
    pass
            await asyncio.sleep(5)
            
            # Print current order books
            order_books = manager.get_all_order_books()
            print(f"\n[{i*5}s] Active order books: {list(order_books.keys())}")
            
            for symbol, ob in order_books.items():
    pass
                metrics = manager.get_metrics(symbol)
                if metrics:
    pass
                    print(f"  {symbol}: spread={metrics['spread_percent']:.4f}%, "
                          f"imbalance={metrics['imbalance']:.2%}")
        
        # Stop manager
        await manager.stop()
        print("\nLevel 2 Manager stopped")
        
    except Exception as e:
    pass
        logger.error(f"Manager demo error: {e}")
        traceback.print_exc()


async def main():
    pass
    """Main demo function"""
    print("\n" + "="*60)
    print("LEVEL 2 (ORDER BOOK) DATA DEMO")
    print("="*60)
    print("\nThis demo shows Level 2 data integration from:")
    print("  1. TickTrader/FXOpen (Forex)")
    print("  2. Binance (Crypto)")
    print("  3. Unified Manager (All sources)")
    
    print("\nSelect demo:")
    print("  1. TickTrader/FXOpen Level 2")
    print("  2. Binance Level 2")
    print("  3. Unified Manager (recommended)")
    print("  4. Run all demos")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
    pass
        await demo_ticktrader()
    elif choice == '2':
    pass
        await demo_binance()
    elif choice == '3':
    pass
        await demo_unified_manager()
    elif choice == '4':
    pass
        await demo_ticktrader()
        await demo_binance()
        await demo_unified_manager()
    else:
    pass
        print("Invalid choice, running unified manager demo...")
        await demo_unified_manager()


if __name__ == "__main__":
    pass
    asyncio.run(main())
