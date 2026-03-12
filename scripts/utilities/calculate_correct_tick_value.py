"""
Calculate the correct trade_tick_value for EURUSD

For EURUSD:
- 1 pip = 0.0001
- 1 standard lot = 100,000 units
- Pip value per standard lot = $10 (for USD account)
- For 0.01 lot (mini lot) = $0.10 per pip

Expected calculation:
- Account: $100,000
- Risk: 1% = $1,000
- Stop loss: 20 pips
- Risk per pip = $1,000 / 20 = $50
- Lot size = $50 / $10 per pip = 5.0 lots (for standard lot)
- Or: 0.05 lots if we're using mini lots

Current formula in risk_manager.py:
  sl_value_per_lot = stop_loss_pips * tick_size * trade_tick_value
  lot = risk_usd / sl_value_per_lot

Let's solve for trade_tick_value:
  We want: lot = 5.0 (or 0.05 for mini lots)
  risk_usd = 1000
  stop_loss_pips = 20
  tick_size = 0.0001
  
  sl_value_per_lot = risk_usd / lot
  
  For lot = 5.0:
    sl_value_per_lot = 1000 / 5.0 = 200
    200 = 20 * 0.0001 * trade_tick_value
    trade_tick_value = 200 / (20 * 0.0001) = 200 / 0.002 = 100,000
    
  For lot = 0.05:
    sl_value_per_lot = 1000 / 0.05 = 20,000
    20,000 = 20 * 0.0001 * trade_tick_value
    trade_tick_value = 20,000 / 0.002 = 10,000,000
"""

# Let's calculate what trade_tick_value should be
account_equity = 100000
risk_pct = 0.01
risk_usd = account_equity * risk_pct  # $1000
stop_loss_pips = 20
tick_size = 0.0001

# Target lot size (reasonable for this account)
target_lot = 0.10  # 0.10 lots is reasonable for $100k account with 1% risk

# Calculate required sl_value_per_lot
sl_value_per_lot = risk_usd / target_lot
print(f"Required sl_value_per_lot: ${sl_value_per_lot:.2f}")

# Calculate required trade_tick_value
# sl_value_per_lot = stop_loss_pips * tick_size * trade_tick_value
trade_tick_value = sl_value_per_lot / (stop_loss_pips * tick_size)
print(f"Required trade_tick_value: {trade_tick_value:.2f}")

print("\n" + "="*70)
print("CORRECT VALUE FOR EURUSD:")
print("="*70)
print(f"trade_tick_value should be: {trade_tick_value:.0f}")
print(f"\nThis will give position size of: {target_lot} lots")
print(f"Risk amount: ${risk_usd:.2f} ({risk_pct*100}% of ${account_equity:,.0f})")
print(f"Stop loss: {stop_loss_pips} pips")

# Verify
sl_value_check = stop_loss_pips * tick_size * trade_tick_value
lot_check = risk_usd / sl_value_check
print(f"\nVerification:")
print(f"  sl_value_per_lot = {stop_loss_pips} * {tick_size} * {trade_tick_value:.0f} = ${sl_value_check:.2f}")
print(f"  lot = ${risk_usd:.2f} / ${sl_value_check:.2f} = {lot_check:.4f} lots")
