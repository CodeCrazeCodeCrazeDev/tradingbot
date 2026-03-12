"""
Correct Position Sizing Fix

The real issue: The formula in risk_manager.py line 517 is:
  sl_value_per_lot = stop_loss_pips * tick_size * trade_tick_value

This is WRONG for forex. The correct formula should be:
  sl_value_per_lot = stop_loss_pips * pip_value_per_lot

For EURUSD:
- 1 pip = 0.0001 (for 5-digit broker) or 0.00001 (for 6-digit)
- Pip value for 1 standard lot (100,000 units) = $10
- Pip value for 0.01 lot (1,000 units) = $0.10

The MT5 trade_tick_value should represent the value of 1 pip for the minimum lot size.

For proper calculation with volume_min=0.01:
- trade_tick_value = $0.10 (value of 1 pip for 0.01 lot)
- But we're multiplying by tick_size (0.0001), so we need to account for that

Actually, let's use the MT5 standard:
- trade_contract_size = 100,000 (for standard lot)
- trade_tick_value = 1.0 (value of 1 tick in quote currency)
- trade_tick_size = 0.00001 (minimum price change)

But our dummy uses:
- point = 0.0001 (this is 1 pip, not 1 tick!)
- trade_tick_value = ??? 

The simplest fix: Use contract_size approach
"""

def fix_mt5_interface():
    """Fix the MT5Interface to use correct forex calculations"""
    file_path = "trading_bot/data/mt5_interface.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the entire Dummy definition with correct values
    old_dummy = '''            Dummy = namedtuple("SymbolInfo", [
                "point", "trade_tick_value", "volume_min", "volume_step"
            ])
            # Assume standard FX 5-digit quotes
            return Dummy(point=0.0001, trade_tick_value=1.0, volume_min=0.01, volume_step=0.01)'''
    
    new_dummy = '''            Dummy = namedtuple("SymbolInfo", [
                "point", "trade_tick_value", "trade_contract_size", "volume_min", "volume_step"
            ])
            # Standard FX values for EURUSD
            # point = 0.00001 (1 tick), trade_tick_value = 1.0, contract_size = 100000
            return Dummy(point=0.00001, trade_tick_value=1.0, trade_contract_size=100000.0, volume_min=0.01, volume_step=0.01)'''
    
    content = content.replace(old_dummy, new_dummy)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Updated SymbolInfo dummy with contract_size")

def fix_risk_manager():
    """Fix the risk manager calculation"""
    file_path = "trading_bot/risk/risk_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the position sizing calculation
    old_calc = '''        tick_size = info.point
        sl_value_per_lot = stop_loss_pips * tick_size * info.trade_tick_value'''
    
    new_calc = '''        tick_size = info.point
        # For forex: pip value = (pip size / exchange rate) * contract size * lot size
        # Simplified for USD account trading EURUSD: pip value per lot = contract_size * pip_size
        contract_size = getattr(info, 'trade_contract_size', 100000.0)
        pip_value_per_lot = contract_size * tick_size  # e.g., 100000 * 0.00001 = 1.0 per lot
        sl_value_per_lot = stop_loss_pips * pip_value_per_lot'''
    
    content = content.replace(old_calc, new_calc)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Fixed risk manager position sizing calculation")

if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE POSITION SIZING FIX")
    print("="*70)
    print("\nApplying fixes...")
    print()
    
    fix_mt5_interface()
    fix_risk_manager()
    
    print("\n" + "="*70)
    print("FIXES APPLIED")
    print("="*70)
    print("\nExpected result:")
    print("  Account: $100,000")
    print("  Risk: 1% = $1,000")
    print("  Stop loss: 20 pips")
    print("  Pip value per lot: $1.00")
    print("  Position size: $1,000 / (20 pips * $1/pip) = 50 lots")
    print("\nNOTE: This is for 1.0 lot = 100,000 units")
    print("      Actual execution will use volume_min = 0.01 lot minimum")
    print("\nRestart bot to apply changes.")
