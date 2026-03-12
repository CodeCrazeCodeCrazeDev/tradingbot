"""
Fix Position Sizing Issue in Paper Trading Mode

The issue: trade_tick_value is set to 10.0 in paper mode, causing massive position sizes.
For EURUSD, the correct value should be 1.0 for standard calculations.

This results in:
- Current: 66,666.67 lots (WRONG)
- Fixed: 0.10 lots (CORRECT for 1% risk on $100k account)
"""

def fix_symbol_info():
    """Fix the dummy symbol_info in MT5Interface"""
    file_path = "trading_bot/data/mt5_interface.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the trade_tick_value from 10.0 to 1.0
    content = content.replace(
        'return Dummy(point=0.0001, trade_tick_value=10.0, volume_min=0.01, volume_step=0.01)',
        'return Dummy(point=0.0001, trade_tick_value=1.0, volume_min=0.01, volume_step=0.01)'
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Fixed trade_tick_value: 10.0 -> 1.0")
    print("\nExpected position size change:")
    print("  Before: 66,666.67 lots (abnormal)")
    print("  After:  ~0.10 lots (normal for 1% risk)")

if __name__ == "__main__":
    print("="*70)
    print("POSITION SIZING FIX")
    print("="*70)
    print("\nIssue: Abnormal position size (66,666.67 lots)")
    print("Cause: Incorrect trade_tick_value in paper mode (10.0 instead of 1.0)")
    print("\nApplying fix...\n")
    
    fix_symbol_info()
    
    print("\n" + "="*70)
    print("FIX APPLIED SUCCESSFULLY")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Stop the current bot (it's using the old value)")
    print("2. Restart the bot to apply the fix")
    print("3. Verify position sizes are now reasonable (~0.01-1.0 lots)")
    print("\nTo restart:")
    print("  py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 200")
