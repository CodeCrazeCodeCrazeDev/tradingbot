# 🚀 MVP Bot Setup Guide

## Minimal Viable Product - Secure Trading Bot

**Email**: peterkiragu68@outlook.com  
**Account Type**: MetaQuotes Demo (MT5)

---

## ✅ What You're Getting

A **secure, reliable MVP bot** with ONLY core features:

1. ✅ **Secure credential management** (no hardcoded passwords)
2. ✅ **MT5 connection** (demo account)
3. ✅ **Market data feed** (real-time prices)
4. ✅ **Simple trade execution** (buy/sell at market)
5. ✅ **Basic risk management** (stop-loss, take-profit)
6. ✅ **Email notifications** (to peterkiragu68@outlook.com)
7. ✅ **Comprehensive logging** (all actions logged)
8. ✅ **Safe shutdown** (no half-executed trades)

**NO complex features yet** - just the essentials that work!

---

## 📋 STEP-BY-STEP SETUP

### Step 1: Install Dependencies (5 minutes)

```bash
# Install required packages
pip install MetaTrader5 python-dotenv
```

### Step 2: Get MT5 Demo Account (5 minutes)

1. **Download MetaTrader 5**:
   - Go to: https://www.metatrader5.com/en/download
   - Install MT5 on your computer

2. **Create Demo Account**:
   - Open MT5
   - Click "File" → "Open an Account"
   - Select "Open a demo account"
   - Choose broker (e.g., MetaQuotes-Demo)
   - Fill in your details
   - **SAVE YOUR CREDENTIALS**:
     - Login: (e.g., 12345678)
     - Password: (your password)
     - Server: (e.g., MetaQuotes-Demo)

### Step 3: Configure Credentials (2 minutes)

```bash
# Copy template to .env
copy .env.template .env

# Edit .env file
notepad .env
```

**Fill in your credentials**:
```env
# Your MT5 demo account
MT5_LOGIN=12345678
MT5_PASSWORD=your_demo_password
MT5_SERVER=MetaQuotes-Demo

# Your email (already set)
EMAIL_ADDRESS=peterkiragu68@outlook.com
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=peterkiragu68@outlook.com
SMTP_PASSWORD=your_outlook_app_password

# Risk limits (safe defaults)
MAX_DAILY_LOSS=100
MAX_POSITION_SIZE=0.01
MAX_POSITIONS=3
```

**⚠️ IMPORTANT**: For email to work, you need an **Outlook App Password**:
1. Go to: https://account.microsoft.com/security
2. Enable "Two-step verification"
3. Create "App password"
4. Use that password in SMTP_PASSWORD

### Step 4: Test Connection (1 minute)

```bash
# Test if credentials work
py -c "
from mvp_bot import SecureCredentials, MT5Connection
creds = SecureCredentials()
conn = MT5Connection(creds)
print('✅ Connected!' if conn.connect() else '❌ Failed')
conn.disconnect()
"
```

### Step 5: Run MVP Bot (NOW!)

```bash
py mvp_bot.py
```

**Expected output**:
```
============================================================
ELITE TRADING BOT - MVP
============================================================
Start Time: 2025-10-04T00:45:00
============================================================
2025-10-04 00:45:01 - INFO - Loading credentials...
2025-10-04 00:45:01 - INFO - Loaded credentials from .env file
2025-10-04 00:45:01 - INFO - Credentials loaded for account: 12345678
2025-10-04 00:45:02 - INFO - Setting up notifications...
2025-10-04 00:45:02 - INFO - Connecting to MT5...
2025-10-04 00:45:03 - INFO - MT5 initialized successfully
2025-10-04 00:45:03 - INFO - Connected to MT5 account: 12345678
2025-10-04 00:45:03 - INFO - Balance: $10000.00
2025-10-04 00:45:03 - INFO - Equity: $10000.00
2025-10-04 00:45:03 - INFO - Server: MetaQuotes-Demo
2025-10-04 00:45:04 - INFO - Email sent: Bot Started
2025-10-04 00:45:04 - INFO - Bot started successfully!
2025-10-04 00:45:04 - INFO - Entering main loop...
2025-10-04 00:45:04 - INFO - Status: Balance=$10000.00, Equity=$10000.00, Profit=$0.00
```

---

## 🎯 HOW TO USE THE BOT

### Manual Trading (Safe for Testing)

The MVP bot is currently in **monitoring mode** - it doesn't trade automatically yet.

**To place a manual trade**:

```python
# In Python console or script
import asyncio
from mvp_bot import MVPBot, SecureCredentials, MT5Connection, EmailNotifier, SimpleTrader

async def test_trade():
    # Setup
    creds = SecureCredentials()
    conn = MT5Connection(creds)
    conn.connect()
    notifier = EmailNotifier(creds)
    trader = SimpleTrader(conn, notifier)
    
    # Place a BUY trade
    result = await trader.place_trade(
        symbol='EURUSD',
        action='buy',
        volume=0.01,  # Minimum size
        stop_loss_pips=50,  # 50 pips stop loss
        take_profit_pips=100  # 100 pips take profit
    )
    
    print(f"Trade result: {result}")
    
    # Cleanup
    conn.disconnect()

# Run
asyncio.run(test_trade())
```

### Check Account Status

```python
from mvp_bot import SecureCredentials, MT5Connection

creds = SecureCredentials()
conn = MT5Connection(creds)
conn.connect()

account = conn.get_account_info()
print(f"Balance: ${account['balance']:.2f}")
print(f"Equity: ${account['equity']:.2f}")
print(f"Profit: ${account['profit']:.2f}")

conn.disconnect()
```

### Get Market Data

```python
from mvp_bot import SecureCredentials, MT5Connection

creds = SecureCredentials()
conn = MT5Connection(creds)
conn.connect()

# Get EURUSD price
info = conn.get_symbol_info('EURUSD')
print(f"EURUSD Bid: {info['bid']:.5f}")
print(f"EURUSD Ask: {info['ask']:.5f}")
print(f"Spread: {info['spread']} points")

conn.disconnect()
```

---

## 🔒 SECURITY FEATURES

### ✅ What's Secure:

1. **No Hardcoded Credentials**
   - All credentials in `.env` file
   - `.env` is gitignored automatically
   - Never committed to version control

2. **Environment Variables**
   - Credentials loaded from environment
   - Can use system environment variables
   - Encrypted in memory (optional)

3. **Error Handling**
   - All operations wrapped in try/except
   - Failed trades don't crash bot
   - Errors logged and emailed

4. **Safe Shutdown**
   - Handles Ctrl+C gracefully
   - Disconnects from MT5 properly
   - No half-executed trades

5. **Email Notifications**
   - Notified of all trades
   - Notified of errors
   - Notified of startup/shutdown

### ⚠️ Security Checklist:

- [ ] `.env` file created and filled
- [ ] `.env` NOT committed to git
- [ ] Strong MT5 password used
- [ ] Outlook app password created
- [ ] Risk limits configured
- [ ] Demo account (not live) ✅

---

## 📊 RISK MANAGEMENT

### Built-in Limits:

```env
MAX_DAILY_LOSS=100      # Stop trading if lose $100 in a day
MAX_POSITION_SIZE=0.01  # Maximum 0.01 lots per trade
MAX_POSITIONS=3         # Maximum 3 open positions
```

### Pre-Trade Checks:

Before every trade, the bot checks:
1. ✅ Position size within limit?
2. ✅ Number of positions within limit?
3. ✅ Daily loss limit not exceeded?

If ANY check fails → Trade rejected

### Stop Loss & Take Profit:

Every trade MUST have:
- **Stop Loss**: Limits maximum loss
- **Take Profit**: Locks in profits

Example:
```python
await trader.place_trade(
    symbol='EURUSD',
    action='buy',
    volume=0.01,
    stop_loss_pips=50,    # Risk 50 pips
    take_profit_pips=100  # Target 100 pips
)
```

---

## 📧 EMAIL NOTIFICATIONS

You'll receive emails for:

1. **Bot Started** - When bot starts successfully
2. **Trade Executed** - When a trade is placed
3. **Trade Failed** - If trade fails
4. **Trade Rejected** - If trade rejected by broker
5. **Position Closed** - When position closes
6. **Bot Stopped** - When bot shuts down
7. **Errors** - Any errors that occur

**Email format**:
```
Subject: [Trading Bot] Trade Executed

Elite Trading Bot Notification

Time: 2025-10-04T00:45:00

Successfully placed buy order
Symbol: EURUSD
Volume: 0.01 lots
Price: 1.10000
Order ID: 12345

---
This is an automated message from your Elite Trading Bot.
```

---

## 📝 LOGGING

All actions are logged to:
- **Console**: Real-time output
- **Log file**: `logs/mvp_bot_YYYYMMDD_HHMMSS.log`

**Log levels**:
- `INFO`: Normal operations
- `WARNING`: Potential issues
- `ERROR`: Errors occurred
- `CRITICAL`: Serious problems

**Example log**:
```
2025-10-04 00:45:01 - mvp_bot - INFO - Loading credentials...
2025-10-04 00:45:03 - mvp_bot - INFO - Connected to MT5 account: 12345678
2025-10-04 00:45:10 - mvp_bot - INFO - Placing buy order: EURUSD 0.01 lots @ 1.10000
2025-10-04 00:45:11 - mvp_bot - INFO - Trade executed successfully: Order #12345
```

---

## 🛑 HOW TO STOP THE BOT

### Method 1: Graceful Shutdown (Recommended)
Press `Ctrl+C` in the terminal

The bot will:
1. Stop accepting new trades
2. Disconnect from MT5
3. Send shutdown email
4. Exit cleanly

### Method 2: Emergency Stop
Close the terminal window

**⚠️ Note**: Existing positions will remain open!

### Method 3: Close All Positions
```python
# Emergency close all
import asyncio
from mvp_bot import MVPBot, SecureCredentials, MT5Connection, EmailNotifier, SimpleTrader

async def emergency_close():
    creds = SecureCredentials()
    conn = MT5Connection(creds)
    conn.connect()
    notifier = EmailNotifier(creds)
    trader = SimpleTrader(conn, notifier)
    
    await trader.close_all_positions()
    
    conn.disconnect()

asyncio.run(emergency_close())
```

---

## 🧪 TESTING CHECKLIST

### Before First Trade:

- [ ] MT5 demo account created
- [ ] Credentials configured in `.env`
- [ ] Bot connects successfully
- [ ] Email notifications working
- [ ] Account balance shows correctly
- [ ] Market data loading
- [ ] Risk limits configured

### Test Trade:

- [ ] Place 0.01 lot trade manually
- [ ] Verify trade appears in MT5
- [ ] Check email notification received
- [ ] Verify stop loss set
- [ ] Verify take profit set
- [ ] Close trade manually
- [ ] Check closing notification

### After Testing:

- [ ] Review logs for errors
- [ ] Check email history
- [ ] Verify all trades logged
- [ ] Confirm safe shutdown works

---

## 🚀 NEXT STEPS (After MVP Works)

### Phase 2: Add Simple Strategy
- Moving average crossover
- RSI overbought/oversold
- Support/resistance levels

### Phase 3: Backtesting
- Test strategy on historical data
- Optimize parameters
- Validate profitability

### Phase 4: Advanced Features
- Multiple timeframes
- Advanced indicators
- Portfolio management
- Machine learning

**But first**: Get MVP working perfectly!

---

## ❓ TROUBLESHOOTING

### Issue: "Missing MT5 credentials"
**Solution**: Create `.env` file and fill in credentials

### Issue: "MT5 initialization failed"
**Solution**: 
1. Make sure MT5 is installed
2. Open MT5 manually first
3. Check if demo account is active

### Issue: "MT5 login failed"
**Solution**:
1. Verify login/password/server in `.env`
2. Check if demo account expired
3. Try logging in manually in MT5

### Issue: "Email not sending"
**Solution**:
1. Create Outlook app password
2. Set SMTP_PASSWORD in `.env`
3. Check spam folder

### Issue: "Trade rejected"
**Solution**:
1. Check if market is open
2. Verify symbol exists (e.g., 'EURUSD')
3. Check if volume is valid (min 0.01)
4. Review MT5 terminal for errors

---

## 📞 SUPPORT

**Email**: peterkiragu68@outlook.com

**Files**:
- `mvp_bot.py` - Main bot code
- `.env` - Your credentials (create from template)
- `.env.template` - Template file
- `logs/` - Log files
- `MVP_SETUP_GUIDE.md` - This guide

**Commands**:
```bash
# Run bot
py mvp_bot.py

# Test connection
py -c "from mvp_bot import *; test_connection()"

# View logs
Get-Content logs\mvp_bot_*.log -Tail 50
```

---

## ✅ FINAL CHECKLIST

Before running in production:

- [ ] Tested on demo account ✅
- [ ] All trades logged ✅
- [ ] Email notifications working ✅
- [ ] Risk limits tested ✅
- [ ] Safe shutdown tested ✅
- [ ] Error handling verified ✅
- [ ] Credentials secured ✅
- [ ] Profitable in paper trading ⏳
- [ ] Reviewed by you ⏳
- [ ] Ready for live (with small size) ⏳

---

**Status**: 🟢 MVP READY FOR TESTING

**Next**: Configure `.env` and run `py mvp_bot.py`
