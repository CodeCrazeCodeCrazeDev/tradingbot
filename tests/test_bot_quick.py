"""
Quick test to see if the thinking bot works
"""
import asyncio
import sys
import pytest

# Skip this test if thinking_bot module doesn't exist
pytest.importorskip("thinking_bot")
from thinking_bot import ThinkingBot

async def test():
    print("=" * 80)
    print("QUICK BOT TEST")
    print("=" * 80)
    
    bot = ThinkingBot()
    print("\n[OK] Bot created")
    
    print("\n1. Initializing...")
    if await bot.initialize():
        print("[OK] Initialization successful")
    else:
        print("[FAIL] Initialization failed")
        return
    
    print("\n2. Testing market analysis...")
    analysis = await bot.analyze_market('EURUSD')
    if analysis:
        print(f"[OK] Analysis complete: {analysis.symbol}")
        print(f"  - Trend: {analysis.trend_direction}")
        print(f"  - RSI: {analysis.rsi:.2f}")
        print(f"  - Price: {analysis.current_price:.5f}")
    else:
        print("[FAIL] Analysis failed")
        return
    
    print("\n3. Testing signal generation...")
    signal = await bot.generate_signal(analysis)
    if signal:
        print(f"[OK] Signal generated: {signal.signal_type.value}")
        print(f"  - Confidence: {signal.confidence:.2f}")
        print(f"  - Entry: {signal.entry_price:.5f}")
        print(f"  - SL: {signal.stop_loss:.5f}")
        print(f"  - TP: {signal.take_profit:.5f}")
    else:
        print("  No signal (market conditions not met)")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE - Bot is working!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test())
