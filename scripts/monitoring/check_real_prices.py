"""
Real Market Price Checker
Compare demo bot prices with actual market prices
"""

import yfinance as yf
from datetime import datetime
import time

def get_real_prices():
    """Fetch real market prices from Yahoo Finance."""
    
    symbols = {
        'EURUSD=X': 'EURUSD',
        'GBPUSD=X': 'GBPUSD', 
        'USDJPY=X': 'USDJPY',
        'AUDUSD=X': 'AUDUSD',
        'USDCAD=X': 'USDCAD'
    }
    
    print("\n" + "=" * 70)
    print(f"📊 REAL MARKET PRICES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    for ticker, name in symbols.items():
        try:
            # Fetch data
            data = yf.Ticker(ticker)
            hist = data.history(period='1d', interval='1m')
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[0]
                high_price = hist['High'].max()
                low_price = hist['Low'].min()
                change = ((current_price - open_price) / open_price) * 100
                
                # Format output
                change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                
                print(f"\n{name}:")
                print(f"  Current: {current_price:.5f}")
                print(f"  Open:    {open_price:.5f}")
                print(f"  High:    {high_price:.5f}")
                print(f"  Low:     {low_price:.5f}")
                print(f"  Change:  {change_symbol} {change:+.2f}%")
            else:
                print(f"\n{name}: No data available")
                
        except Exception as e:
            print(f"\n{name}: Error - {e}")
    
    print("\n" + "=" * 70)
    print("💡 These are REAL market prices from Yahoo Finance")
    print("💡 Compare with your demo bot prices in logs/demo_trading.log")
    print("=" * 70 + "\n")


def compare_with_demo():
    """Compare real prices with demo bot prices."""
    
    print("\n" + "=" * 70)
    print("🔍 DEMO BOT vs REAL MARKET COMPARISON")
    print("=" * 70)
    
    # Read last demo prices from log
    try:
        with open('logs/demo_trading.log', 'r') as f:
            lines = f.readlines()
            
        # Find recent price lines
        demo_prices = {}
        for line in reversed(lines[-100:]):  # Check last 100 lines
            if 'Price:' in line and 'INFO' in line:
                parts = line.split('Price:')
                if len(parts) > 1:
                    price_str = parts[1].strip()
                    try:
                        price = float(price_str)
                        # Try to identify symbol from context
                        for prev_line in reversed(lines[max(0, lines.index(line)-5):lines.index(line)]):
                            if 'ANALYZING:' in prev_line:
                                symbol = prev_line.split('ANALYZING:')[1].strip()
                                demo_prices[symbol] = price
                                break
                    except:
                        pass
        
        if demo_prices:
            print("\nDemo Bot Prices (Simulated):")
            for symbol, price in demo_prices.items():
                print(f"  {symbol}: {price:.5f}")
        else:
            print("\nNo demo prices found in log (bot may not be running)")
            
    except FileNotFoundError:
        print("\nDemo trading log not found")
    except Exception as e:
        print(f"\nError reading demo log: {e}")
    
    print("\n" + "=" * 70)


def continuous_monitor():
    """Continuously monitor and display prices."""
    
    print("\n" + "=" * 70)
    print("🔄 CONTINUOUS PRICE MONITORING")
    print("=" * 70)
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            get_real_prices()
            print("⏳ Refreshing in 30 seconds...\n")
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped\n")


if __name__ == '__main__':
    import sys
    
    print("\n" + "=" * 70)
    print("📊 Real Market Price Checker")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Check prices once")
    print("  2. Compare with demo bot")
    print("  3. Continuous monitoring (updates every 30s)")
    print("  4. Exit")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            get_real_prices()
        elif choice == '2':
            get_real_prices()
            compare_with_demo()
        elif choice == '3':
            continuous_monitor()
        elif choice == '4':
            print("\n✅ Goodbye!\n")
        else:
            print("\n❌ Invalid choice\n")
            
    except KeyboardInterrupt:
        print("\n\n✅ Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
